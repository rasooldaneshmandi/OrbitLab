from threading import Lock

import numpy as np

from sdr.device import ComplexArray


class IQCircularBuffer:
    """
    Thread-safe circular buffer for complex IQ samples.

    The buffer always retains the newest samples. When incoming data
    exceeds the remaining capacity, the oldest samples are overwritten.

    Typical data flow:

        SDR Device
            |
            v
        IQCircularBuffer
            |
            +--> Spectrum
            +--> Waterfall
            +--> IQ Recorder
            +--> Demodulator
            +--> Doppler Estimator
    """

    def __init__(
        self,
        capacity: int,
        dtype: np.dtype = np.complex64,
    ):
        if not isinstance(capacity, int):
            raise TypeError(
                "capacity must be an integer."
            )

        if capacity <= 0:
            raise ValueError(
                "capacity must be greater than zero."
            )

        if not np.issubdtype(dtype, np.complexfloating):
            raise TypeError(
                "IQ buffer dtype must be a complex type."
            )

        self._capacity = capacity
        self._dtype = np.dtype(dtype)

        self._buffer = np.zeros(
            capacity,
            dtype=self._dtype,
        )

        self._write_index = 0
        self._sample_count = 0
        self._total_samples_written = 0

        self._lock = Lock()

    @property
    def capacity(self) -> int:
        """
        Return the maximum number of stored samples.
        """
        return self._capacity

    @property
    def dtype(self) -> np.dtype:
        """
        Return the NumPy data type used by the buffer.
        """
        return self._dtype

    @property
    def size(self) -> int:
        """
        Return the number of valid samples currently stored.
        """
        with self._lock:
            return self._sample_count

    @property
    def available_samples(self) -> int:
        """
        Alias for the number of valid stored samples.
        """
        return self.size

    @property
    def free_space(self) -> int:
        """
        Return the number of unused buffer positions.
        """
        with self._lock:
            return self._capacity - self._sample_count

    @property
    def total_samples_written(self) -> int:
        """
        Return the total number of samples written since creation
        or the last statistics reset.
        """
        with self._lock:
            return self._total_samples_written

    @property
    def is_full(self) -> bool:
        """
        Return True when the buffer is at full capacity.
        """
        with self._lock:
            return self._sample_count == self._capacity

    @property
    def is_empty(self) -> bool:
        """
        Return True when no valid samples are stored.
        """
        with self._lock:
            return self._sample_count == 0

    def write(
        self,
        samples: ComplexArray,
    ) -> int:
        """
        Write IQ samples into the circular buffer.

        If more samples than the total capacity are provided, only the
        newest `capacity` samples are retained.

        Returns:
            Number of input samples accepted.
        """
        iq_samples = np.asarray(
            samples,
            dtype=self._dtype,
        )

        if iq_samples.ndim != 1:
            raise ValueError(
                "IQ samples must be a one-dimensional array."
            )

        input_sample_count = iq_samples.size

        if input_sample_count == 0:
            return 0

        with self._lock:
            self._total_samples_written += (
                input_sample_count
            )

            if input_sample_count >= self._capacity:
                newest_samples = iq_samples[
                    -self._capacity:
                ]

                self._buffer[:] = newest_samples
                self._write_index = 0
                self._sample_count = self._capacity

                return input_sample_count

            first_part_length = min(
                input_sample_count,
                self._capacity - self._write_index,
            )

            second_part_length = (
                input_sample_count - first_part_length
            )

            self._buffer[
                self._write_index:
                self._write_index + first_part_length
            ] = iq_samples[:first_part_length]

            if second_part_length > 0:
                self._buffer[
                    :second_part_length
                ] = iq_samples[first_part_length:]

            self._write_index = (
                self._write_index
                + input_sample_count
            ) % self._capacity

            self._sample_count = min(
                self._capacity,
                self._sample_count + input_sample_count,
            )

        return input_sample_count

    def read_latest(
        self,
        num_samples: int,
        *,
        allow_partial: bool = False,
    ) -> ComplexArray:
        """
        Return the newest IQ samples without removing them.

        Args:
            num_samples:
                Requested number of samples.

            allow_partial:
                If False, an exception is raised when fewer samples are
                available. If True, all available samples are returned.

        Returns:
            A copy of the requested samples in chronological order,
            from oldest to newest.
        """
        self._validate_read_size(num_samples)

        with self._lock:
            if self._sample_count < num_samples:
                if not allow_partial:
                    raise BufferError(
                        f"Requested {num_samples} IQ samples, "
                        f"but only {self._sample_count} are available."
                    )

                num_samples = self._sample_count

            if num_samples == 0:
                return np.empty(
                    0,
                    dtype=self._dtype,
                )

            start_index = (
                self._write_index - num_samples
            ) % self._capacity

            return self._copy_range(
                start_index=start_index,
                length=num_samples,
            )

    def read_all(self) -> ComplexArray:
        """
        Return all valid samples without removing them.

        Samples are returned from oldest to newest.
        """
        with self._lock:
            if self._sample_count == 0:
                return np.empty(
                    0,
                    dtype=self._dtype,
                )

            oldest_index = (
                self._write_index
                - self._sample_count
            ) % self._capacity

            return self._copy_range(
                start_index=oldest_index,
                length=self._sample_count,
            )

    def pop_oldest(
        self,
        num_samples: int,
        *,
        allow_partial: bool = False,
    ) -> ComplexArray:
        """
        Return and remove the oldest IQ samples.

        This is useful for streaming consumers such as decoders or
        file writers.
        """
        self._validate_read_size(num_samples)

        with self._lock:
            if self._sample_count < num_samples:
                if not allow_partial:
                    raise BufferError(
                        f"Requested {num_samples} IQ samples, "
                        f"but only {self._sample_count} are available."
                    )

                num_samples = self._sample_count

            if num_samples == 0:
                return np.empty(
                    0,
                    dtype=self._dtype,
                )

            oldest_index = (
                self._write_index
                - self._sample_count
            ) % self._capacity

            result = self._copy_range(
                start_index=oldest_index,
                length=num_samples,
            )

            self._sample_count -= num_samples

            return result

    def clear(self) -> None:
        """
        Remove all stored samples.
        """
        with self._lock:
            self._buffer.fill(0)
            self._write_index = 0
            self._sample_count = 0

    def reset_statistics(self) -> None:
        """
        Reset the total-samples-written counter.
        """
        with self._lock:
            self._total_samples_written = 0

    def _copy_range(
        self,
        start_index: int,
        length: int,
    ) -> ComplexArray:
        """
        Copy a chronological range from the circular buffer.

        This method must only be called while the buffer lock is held.
        """
        end_index = start_index + length

        if end_index <= self._capacity:
            return self._buffer[
                start_index:end_index
            ].copy()

        first_part = self._buffer[
            start_index:
        ]

        second_part_length = (
            end_index - self._capacity
        )

        second_part = self._buffer[
            :second_part_length
        ]

        return np.concatenate(
            (
                first_part,
                second_part,
            )
        ).astype(
            self._dtype,
            copy=False,
        )

    @staticmethod
    def _validate_read_size(
        num_samples: int,
    ) -> None:
        """
        Validate a requested sample count.
        """
        if not isinstance(num_samples, int):
            raise TypeError(
                "num_samples must be an integer."
            )

        if num_samples < 0:
            raise ValueError(
                "num_samples cannot be negative."
            )

    def __len__(self) -> int:
        """
        Return the number of valid stored IQ samples.
        """
        return self.size

    def __repr__(self) -> str:
        return (
            "IQCircularBuffer("
            f"capacity={self.capacity}, "
            f"size={self.size}, "
            f"dtype={self.dtype}"
            ")"
        )