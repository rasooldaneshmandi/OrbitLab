from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any

import numpy as np
from numpy.typing import NDArray

from sdr.device import SDRDevice
from sdr.iq_buffer import IQCircularBuffer
from sdr.spectrum import SpectrumAnalyzer


ComplexArray = NDArray[np.complex64]
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class SDRPipelineStatus:
    running: bool
    sample_rate_hz: float
    center_frequency_hz: float
    buffer_capacity: int
    buffered_samples: int
    acquisition_block_size: int
    fft_size: int
    total_acquisition_cycles: int
    total_samples_acquired: int
    total_spectra_computed: int


class SDRPipeline:
    """
    SDR acquisition and spectrum-processing pipeline.

    Processing chain:

        SDRDevice
            ↓
        IQCircularBuffer
            ↓
        SpectrumAnalyzer
            ↓
        GUI / Waterfall / Recorder
    """

    def __init__(
        self,
        device: SDRDevice,
        *,
        buffer_capacity: int = 65_536,
        acquisition_block_size: int = 4096,
        fft_size: int = 4096,
    ) -> None:
        if device is None:
            raise ValueError("device cannot be None.")

        self._validate_positive_int(
            buffer_capacity,
            "buffer_capacity",
        )
        self._validate_positive_int(
            acquisition_block_size,
            "acquisition_block_size",
        )
        self._validate_positive_int(
            fft_size,
            "fft_size",
        )

        if fft_size > buffer_capacity:
            raise ValueError(
                "fft_size cannot be greater than buffer_capacity."
            )

        self._device = device

        self._buffer = IQCircularBuffer(
            capacity=buffer_capacity,
            dtype=np.complex64,
        )

        self._acquisition_block_size = acquisition_block_size
        self._fft_size = fft_size

        self._running = False
        self._lock = RLock()

        self._latest_frequencies_hz: FloatArray = np.empty(
            0,
            dtype=np.float64,
        )

        self._latest_power_db: FloatArray = np.empty(
            0,
            dtype=np.float64,
        )

        self._latest_peak_frequency_hz: float | None = None
        self._latest_peak_power_db: float | None = None

        self._total_acquisition_cycles = 0
        self._total_samples_acquired = 0
        self._total_spectra_computed = 0

    # ================================================================
    # Basic properties
    # ================================================================

    @property
    def device(self) -> SDRDevice:
        return self._device

    @property
    def buffer(self) -> IQCircularBuffer:
        return self._buffer

    @property
    def is_running(self) -> bool:
        return self._running and self._device_is_running()

    @property
    def sample_rate_hz(self) -> float:
        return float(
            self._read_device_attribute("sample_rate")
        )

    @property
    def center_frequency_hz(self) -> float:
        return float(
            self._read_device_attribute("center_frequency")
        )

    @property
    def buffer_capacity(self) -> int:
        return int(self._buffer.capacity)

    @property
    def buffered_samples(self) -> int:
        return int(self._buffer.size)

    @property
    def acquisition_block_size(self) -> int:
        return self._acquisition_block_size

    @property
    def fft_size(self) -> int:
        return self._fft_size

    # ================================================================
    # Spectrum properties
    # ================================================================

    @property
    def latest_peak_frequency_hz(self) -> float | None:
        return self._latest_peak_frequency_hz

    @property
    def latest_peak_power_db(self) -> float | None:
        return self._latest_peak_power_db

    @property
    def latest_peak_rf_frequency_hz(
        self,
    ) -> float | None:
        if self._latest_peak_frequency_hz is None:
            return None

        return (
            self.center_frequency_hz
            + self._latest_peak_frequency_hz
        )

    # ================================================================
    # Statistics
    # ================================================================

    @property
    def total_acquisition_cycles(self) -> int:
        return self._total_acquisition_cycles

    @property
    def acquisition_blocks(self) -> int:
        return self._total_acquisition_cycles

    @property
    def total_samples_acquired(self) -> int:
        return self._total_samples_acquired

    @property
    def total_spectra_computed(self) -> int:
        return self._total_spectra_computed

    @property
    def status(self) -> SDRPipelineStatus:
        return SDRPipelineStatus(
            running=self.is_running,
            sample_rate_hz=self.sample_rate_hz,
            center_frequency_hz=self.center_frequency_hz,
            buffer_capacity=self.buffer_capacity,
            buffered_samples=self.buffered_samples,
            acquisition_block_size=self.acquisition_block_size,
            fft_size=self.fft_size,
            total_acquisition_cycles=(
                self.total_acquisition_cycles
            ),
            total_samples_acquired=(
                self.total_samples_acquired
            ),
            total_spectra_computed=(
                self.total_spectra_computed
            ),
        )

    # ================================================================
    # Lifecycle
    # ================================================================

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return

            start_method = getattr(
                self._device,
                "start",
                None,
            )

            if not callable(start_method):
                raise AttributeError(
                    "SDR device does not implement start()."
                )

            start_method()
            self._running = True

            if not self._device_is_running():
                self._running = False

                raise RuntimeError(
                    "SDR device did not enter running state."
                )

    def stop(self) -> None:
        with self._lock:
            stop_method = getattr(
                self._device,
                "stop",
                None,
            )

            if callable(stop_method):
                stop_method()

            self._running = False

    # ================================================================
    # Acquisition
    # ================================================================

    def acquire(
        self,
        num_samples: int | None = None,
    ) -> int:
        """
        Acquire IQ samples and write them into the circular buffer.

        Returns:
            Number of acquired IQ samples.
        """
        if num_samples is None:
            num_samples = self._acquisition_block_size

        self._validate_positive_int(
            num_samples,
            "num_samples",
        )

        if not self.is_running:
            self.start()

        read_method = getattr(
            self._device,
            "read_samples",
            None,
        )

        if not callable(read_method):
            raise AttributeError(
                "SDR device does not implement read_samples()."
            )

        raw_samples = read_method(num_samples)

        iq_samples = self._validate_iq_samples(
            raw_samples
        )

        with self._lock:
            self._buffer.write(iq_samples)

            sample_count = int(iq_samples.size)

            self._total_acquisition_cycles += 1
            self._total_samples_acquired += sample_count

        return sample_count

    def update(self) -> bool:
        """
        Execute one complete pipeline cycle.

        The method:

        1. Acquires one IQ block.
        2. Stores it in the circular buffer.
        3. Computes a spectrum when enough samples are available.

        Returns:
            True when a new spectrum was computed.
            False when fewer than fft_size samples are buffered.
        """
        self.acquire()

        with self._lock:
            if self._buffer.size < self._fft_size:
                return False

            fft_samples = self._buffer.read_latest(
                self._fft_size
            )

            frequencies_hz, power_db = (
                SpectrumAnalyzer.compute_fft(
                    fft_samples,
                    self.sample_rate_hz,
                )
            )

            frequencies_hz = np.asarray(
                frequencies_hz,
                dtype=np.float64,
            )

            power_db = np.asarray(
                power_db,
                dtype=np.float64,
            )

            self._validate_spectrum(
                frequencies_hz,
                power_db,
            )

            self._latest_frequencies_hz = frequencies_hz
            self._latest_power_db = power_db

            peak_index = int(np.argmax(power_db))

            self._latest_peak_frequency_hz = float(
                frequencies_hz[peak_index]
            )

            self._latest_peak_power_db = float(
                power_db[peak_index]
            )

            self._total_spectra_computed += 1

            return True

    # ================================================================
    # Spectrum access
    # ================================================================

    def has_spectrum(self) -> bool:
        with self._lock:
            return (
                self._latest_frequencies_hz.size > 0
                and self._latest_power_db.size > 0
            )

    def latest_spectrum(
        self,
        *,
        update: bool = True,
    ) -> tuple[FloatArray, FloatArray]:
        if update:
            self.update()

        with self._lock:
            return (
                self._latest_frequencies_hz.copy(),
                self._latest_power_db.copy(),
            )

    def latest_rf_spectrum(
        self,
        *,
        update: bool = True,
    ) -> tuple[FloatArray, FloatArray]:
        frequencies_hz, power_db = (
            self.latest_spectrum(update=update)
        )

        if frequencies_hz.size == 0:
            return frequencies_hz, power_db

        return (
            frequencies_hz
            + self.center_frequency_hz,
            power_db,
        )

    # ================================================================
    # IQ access
    # ================================================================

    def latest_iq(
        self,
        num_samples: int | None = None,
        *,
        allow_partial: bool = True,
    ) -> ComplexArray:
        with self._lock:
            available = int(self._buffer.size)

            if available == 0:
                return np.empty(
                    0,
                    dtype=np.complex64,
                )

            if num_samples is None:
                samples = self._buffer.read_all()

                return np.asarray(
                    samples,
                    dtype=np.complex64,
                )

            self._validate_positive_int(
                num_samples,
                "num_samples",
            )

            if (
                not allow_partial
                and available < num_samples
            ):
                raise ValueError(
                    "Not enough IQ samples are available."
                )

            count = min(
                num_samples,
                available,
            )

            samples = self._buffer.read_latest(count)

            return np.asarray(
                samples,
                dtype=np.complex64,
            )

    # ================================================================
    # Configuration
    # ================================================================

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        frequency_hz = float(frequency_hz)

        if not np.isfinite(frequency_hz):
            raise ValueError(
                "frequency_hz must be finite."
            )

        if frequency_hz <= 0:
            raise ValueError(
                "frequency_hz must be greater than zero."
            )

        setter = getattr(
            self._device,
            "set_center_frequency",
            None,
        )

        if not callable(setter):
            raise AttributeError(
                "SDR device does not implement "
                "set_center_frequency()."
            )

        with self._lock:
            setter(frequency_hz)
            self._clear_spectrum()

    def set_fft_size(
        self,
        fft_size: int,
    ) -> None:
        self._validate_positive_int(
            fft_size,
            "fft_size",
        )

        if fft_size > self._buffer.capacity:
            raise ValueError(
                "fft_size cannot exceed buffer capacity."
            )

        with self._lock:
            self._fft_size = fft_size
            self._clear_spectrum()

    def set_acquisition_block_size(
        self,
        block_size: int,
    ) -> None:
        self._validate_positive_int(
            block_size,
            "block_size",
        )

        with self._lock:
            self._acquisition_block_size = block_size

    # ================================================================
    # Reset
    # ================================================================

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._clear_spectrum()

    def reset(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._clear_spectrum()

            self._total_acquisition_cycles = 0
            self._total_samples_acquired = 0
            self._total_spectra_computed = 0

            reset_phase = getattr(
                self._device,
                "reset_phase",
                None,
            )

            if callable(reset_phase):
                reset_phase()

    def _clear_spectrum(self) -> None:
        self._latest_frequencies_hz = np.empty(
            0,
            dtype=np.float64,
        )

        self._latest_power_db = np.empty(
            0,
            dtype=np.float64,
        )

        self._latest_peak_frequency_hz = None
        self._latest_peak_power_db = None

    # ================================================================
    # Helpers
    # ================================================================

    def _device_is_running(self) -> bool:
        attribute = getattr(
            self._device,
            "is_running",
            False,
        )

        if callable(attribute):
            return bool(attribute())

        return bool(attribute)

    def _read_device_attribute(
        self,
        attribute_name: str,
    ) -> Any:
        attribute = getattr(
            self._device,
            attribute_name,
            None,
        )

        if attribute is None:
            raise AttributeError(
                f"SDR device does not provide "
                f"{attribute_name}."
            )

        if callable(attribute):
            return attribute()

        return attribute

    @staticmethod
    def _validate_positive_int(
        value: int,
        name: str,
    ) -> None:
        if isinstance(value, bool) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

    @staticmethod
    def _validate_iq_samples(
        samples: Any,
    ) -> ComplexArray:
        array = np.asarray(samples)

        if array.ndim != 1:
            raise ValueError(
                "IQ samples must be one-dimensional."
            )

        if array.size == 0:
            raise ValueError(
                "SDR device returned no IQ samples."
            )

        if not np.iscomplexobj(array):
            raise TypeError(
                "SDR device must return complex IQ samples."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                "IQ samples contain NaN or infinite values."
            )

        return np.asarray(
            array,
            dtype=np.complex64,
        )

    @staticmethod
    def _validate_spectrum(
        frequencies_hz: FloatArray,
        power_db: FloatArray,
    ) -> None:
        if frequencies_hz.ndim != 1:
            raise ValueError(
                "Frequency axis must be one-dimensional."
            )

        if power_db.ndim != 1:
            raise ValueError(
                "Power spectrum must be one-dimensional."
            )

        if frequencies_hz.size == 0:
            raise ValueError(
                "Spectrum cannot be empty."
            )

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have "
                "the same size."
            )

        if not np.all(np.isfinite(frequencies_hz)):
            raise ValueError(
                "Frequency axis contains invalid values."
            )

        if not np.all(np.isfinite(power_db)):
            raise ValueError(
                "Power spectrum contains invalid values."
            )

    def __enter__(self) -> SDRPipeline:
        self.start()
        return self

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> None:
        self.stop()

    def __repr__(self) -> str:
        return (
            "SDRPipeline("
            f"device={self._device.__class__.__name__}, "
            f"running={self.is_running}, "
            f"sample_rate_hz={self.sample_rate_hz}, "
            f"center_frequency_hz={self.center_frequency_hz}, "
            f"buffered_samples={self.buffered_samples}, "
            f"fft_size={self.fft_size}"
            ")"
        )