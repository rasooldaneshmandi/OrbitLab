from __future__ import annotations

import numpy as np

from sdr.device import ComplexArray, SDRDevice

try:
    import adi
except ImportError as _import_error:  # pragma: no cover - depends on host setup
    adi = None
    _IMPORT_ERROR: Exception | None = _import_error
else:
    _IMPORT_ERROR = None


VALID_GAIN_MODES = (
    "manual",
    "slow_attack",
    "fast_attack",
    "hybrid",
)


class PlutoSDRDevice(SDRDevice):
    """
    SDRDevice implementation for the Analog Devices ADALM-PLUTO (PlutoSDR),
    built on top of Analog Devices' `pyadi-iio` / `libiio` bindings.

    Drop-in replacement for SDRSimulator: anything built against the
    SDRDevice interface (SDRPipeline, DopplerController, ...) works
    unchanged with real hardware.

    Requirements (not installed by default):

        pip install pyadi-iio

        The host also needs `libiio` (and, for AD936x boards,
        `libad9361-iio`) installed, and the Pluto reachable either
        over USB (uri="usb:...") or the network (uri="ip:192.168.2.1",
        the factory-default address).

    Typical usage:

        pluto = PlutoSDRDevice(
            uri="ip:192.168.2.1",
            sample_rate_hz=2_000_000.0,
            center_frequency_hz=437_000_000.0,
        )

        pipeline = SDRPipeline(device=pluto, ...)

        doppler_controller = DopplerController(
            tracker=tracker,
            receiver=pluto,
            nominal_frequency_hz=437_000_000.0,
        )
    """

    DEFAULT_URI = "ip:192.168.2.1"

    def __init__(
        self,
        uri: str = DEFAULT_URI,
        sample_rate_hz: float = 2_000_000.0,
        center_frequency_hz: float = 437_000_000.0,
        bandwidth_hz: float | None = None,
        buffer_size: int = 4096,
        gain_control_mode: str = "slow_attack",
        manual_gain_db: float = 40.0,
    ) -> None:
        """
        Args:
            uri:
                libiio context URI. "ip:192.168.2.1" for the default
                USB-Ethernet gadget address, "usb:<bus>.<addr>.<if>"
                for native USB, or "ip:<hostname/ip>" on a LAN.

            sample_rate_hz:
                RX sample rate. The Pluto's AD9363 supports roughly
                520 kHz to 61.44 MHz (upstream firmware/config dependent).

            center_frequency_hz:
                RX local-oscillator (tuner) frequency.

            bandwidth_hz:
                RX analog filter bandwidth. Defaults to sample_rate_hz.

            buffer_size:
                Number of complex samples returned per rx() call.

            gain_control_mode:
                One of "manual", "slow_attack", "fast_attack", "hybrid".

            manual_gain_db:
                Hardware gain used only when gain_control_mode == "manual".
        """
        if adi is None:
            raise ImportError(
                "pyadi-iio is required for PlutoSDRDevice. "
                "Install it with: pip install pyadi-iio "
                "(and make sure libiio is installed on this system)."
            ) from _IMPORT_ERROR

        if sample_rate_hz <= 0.0:
            raise ValueError(
                "sample_rate_hz must be greater than zero."
            )

        if center_frequency_hz <= 0.0:
            raise ValueError(
                "center_frequency_hz must be greater than zero."
            )

        if buffer_size <= 0:
            raise ValueError(
                "buffer_size must be greater than zero."
            )

        if gain_control_mode not in VALID_GAIN_MODES:
            raise ValueError(
                f"gain_control_mode must be one of {VALID_GAIN_MODES}."
            )

        self._uri = str(uri)
        self._sample_rate_hz = float(sample_rate_hz)
        self._center_frequency_hz = float(center_frequency_hz)
        self._bandwidth_hz = float(
            bandwidth_hz if bandwidth_hz is not None else sample_rate_hz
        )
        self._buffer_size = int(buffer_size)
        self._gain_control_mode = gain_control_mode
        self._manual_gain_db = float(manual_gain_db)

        self._sdr = None
        self._running = False

    # ================================================================
    # SDRDevice interface
    # ================================================================

    def start(self) -> None:
        """
        Open the libiio context and configure the RX chain.
        Safe to call again if already running (no-op).
        """
        if self._running:
            return

        self._sdr = adi.Pluto(uri=self._uri)

        self._sdr.sample_rate = int(self._sample_rate_hz)
        self._sdr.rx_rf_bandwidth = int(self._bandwidth_hz)
        self._sdr.rx_lo = int(self._center_frequency_hz)
        self._sdr.rx_buffer_size = self._buffer_size

        self._sdr.gain_control_mode_chan0 = self._gain_control_mode

        if self._gain_control_mode == "manual":
            self._sdr.rx_hardwaregain_chan0 = self._manual_gain_db

        self._running = True

    def stop(self) -> None:
        """
        Release the libiio context. A subsequent start() or
        read_samples() re-opens it.
        """
        self._sdr = None
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def read_samples(
        self,
        num_samples: int,
    ) -> ComplexArray:
        if not isinstance(num_samples, int):
            raise TypeError(
                "num_samples must be an integer."
            )

        if num_samples <= 0:
            raise ValueError(
                "num_samples must be greater than zero."
            )

        if not self._running:
            self.start()

        # Pluto streams fixed-size blocks; resize the hardware buffer
        # when the caller asks for a different amount than currently set.
        if num_samples != self._buffer_size:
            self._sdr.rx_buffer_size = num_samples
            self._buffer_size = num_samples

        samples = self._sdr.rx()

        return np.asarray(
            samples,
            dtype=np.complex64,
        )

    def sample_rate(self) -> float:
        return self._sample_rate_hz

    def center_frequency(self) -> float:
        return self._center_frequency_hz

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        frequency_hz = float(frequency_hz)

        if frequency_hz <= 0.0:
            raise ValueError(
                "Center frequency must be greater than zero."
            )

        self._center_frequency_hz = frequency_hz

        if self._sdr is not None:
            self._sdr.rx_lo = int(frequency_hz)

    # ================================================================
    # Pluto-specific extras (outside the SDRDevice ABC)
    # ================================================================

    def set_sample_rate(
        self,
        sample_rate_hz: float,
    ) -> None:
        sample_rate_hz = float(sample_rate_hz)

        if sample_rate_hz <= 0.0:
            raise ValueError(
                "sample_rate_hz must be greater than zero."
            )

        self._sample_rate_hz = sample_rate_hz

        if self._sdr is not None:
            self._sdr.sample_rate = int(sample_rate_hz)

    def set_bandwidth(
        self,
        bandwidth_hz: float,
    ) -> None:
        bandwidth_hz = float(bandwidth_hz)

        if bandwidth_hz <= 0.0:
            raise ValueError(
                "bandwidth_hz must be greater than zero."
            )

        self._bandwidth_hz = bandwidth_hz

        if self._sdr is not None:
            self._sdr.rx_rf_bandwidth = int(bandwidth_hz)

    def set_manual_gain(
        self,
        gain_db: float,
    ) -> None:
        """
        Switch to manual gain control and apply a fixed hardware gain.
        """
        self._gain_control_mode = "manual"
        self._manual_gain_db = float(gain_db)

        if self._sdr is not None:
            self._sdr.gain_control_mode_chan0 = "manual"
            self._sdr.rx_hardwaregain_chan0 = self._manual_gain_db

    def set_agc(
        self,
        mode: str = "slow_attack",
    ) -> None:
        """
        Switch to one of the automatic gain-control modes
        ("slow_attack", "fast_attack", "hybrid").
        """
        if mode not in VALID_GAIN_MODES or mode == "manual":
            raise ValueError(
                "mode must be one of 'slow_attack', 'fast_attack', 'hybrid'."
            )

        self._gain_control_mode = mode

        if self._sdr is not None:
            self._sdr.gain_control_mode_chan0 = mode

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def bandwidth_hz(self) -> float:
        return self._bandwidth_hz

    @property
    def gain_control_mode(self) -> str:
        return self._gain_control_mode
