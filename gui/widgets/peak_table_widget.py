from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class SpectrumPeak:
    """
    One detected spectrum peak.
    """

    frequency_hz: float
    power_db: float
    bin_index: int


class PeakTableWidget(QWidget):
    """
    Displays the strongest local peaks in a spectrum.

    Features:
        - Local-maximum detection
        - Configurable number of peaks
        - Minimum peak separation
        - Minimum power threshold
        - Sorting by power
        - Double-click to select a peak
    """

    peak_selected = pyqtSignal(float, float)

    def __init__(
        self,
        *,
        maximum_peaks: int = 10,
        minimum_distance_bins: int = 20,
        minimum_power_db: float = -120.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._maximum_peaks = self._validate_positive_int(
            maximum_peaks,
            "maximum_peaks",
        )

        self._minimum_distance_bins = self._validate_positive_int(
            minimum_distance_bins,
            "minimum_distance_bins",
        )

        self._minimum_power_db = float(
            minimum_power_db
        )

        self._latest_peaks: list[SpectrumPeak] = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Strongest Spectrum Peaks"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._maximum_peaks_spin = QSpinBox()
        self._maximum_peaks_spin.setRange(
            1,
            100,
        )
        self._maximum_peaks_spin.setValue(
            self._maximum_peaks
        )

        self._minimum_distance_spin = QSpinBox()
        self._minimum_distance_spin.setRange(
            1,
            4096,
        )
        self._minimum_distance_spin.setValue(
            self._minimum_distance_bins
        )

        self._refresh_button = QPushButton(
            "Refresh"
        )

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(
            QLabel("Maximum peaks:")
        )
        controls_layout.addWidget(
            self._maximum_peaks_spin
        )

        controls_layout.addWidget(
            QLabel("Minimum distance [bins]:")
        )
        controls_layout.addWidget(
            self._minimum_distance_spin
        )

        controls_layout.addStretch(1)

        controls_layout.addWidget(
            self._refresh_button
        )

        self._table = QTableWidget(
            0,
            4,
        )

        self._table.setHorizontalHeaderLabels(
            [
                "#",
                "Frequency [MHz]",
                "Power [dB]",
                "FFT Bin",
            ]
        )

        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self._table.setAlternatingRowColors(
            True
        )

        header = self._table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self._status_label = QLabel(
            "Waiting for spectrum data..."
        )

        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout = QVBoxLayout(self)

        layout.addWidget(
            self._title_label
        )

        layout.addLayout(
            controls_layout
        )

        layout.addWidget(
            self._table,
            stretch=1,
        )

        layout.addWidget(
            self._status_label
        )

    def _connect_signals(self) -> None:
        self._maximum_peaks_spin.valueChanged.connect(
            self._on_configuration_changed
        )

        self._minimum_distance_spin.valueChanged.connect(
            self._on_configuration_changed
        )

        self._table.cellDoubleClicked.connect(
            self._on_row_double_clicked
        )

    def _on_configuration_changed(
        self,
        value: int,
    ) -> None:
        del value

        self._maximum_peaks = int(
            self._maximum_peaks_spin.value()
        )

        self._minimum_distance_bins = int(
            self._minimum_distance_spin.value()
        )

    def update_spectrum(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
    ) -> list[SpectrumPeak]:
        """
        Detect and display the strongest spectrum peaks.
        """
        frequencies_hz = np.asarray(
            frequencies_hz,
            dtype=np.float64,
        )

        power_db = np.asarray(
            power_db,
            dtype=np.float64,
        )

        if frequencies_hz.ndim != 1:
            raise ValueError(
                "frequencies_hz must be one-dimensional."
            )

        if power_db.ndim != 1:
            raise ValueError(
                "power_db must be one-dimensional."
            )

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have equal size."
            )

        if frequencies_hz.size < 3:
            self.clear()
            return []

        self._latest_peaks = self._detect_peaks(
            frequencies_hz,
            power_db,
        )

        self._populate_table(
            self._latest_peaks
        )

        return list(
            self._latest_peaks
        )

    def _detect_peaks(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
    ) -> list[SpectrumPeak]:
        """
        Detect local maxima without requiring SciPy.
        """
        local_maximum_mask = (
            (power_db[1:-1] > power_db[:-2])
            & (power_db[1:-1] >= power_db[2:])
            & (
                power_db[1:-1]
                >= self._minimum_power_db
            )
        )

        candidate_indices = (
            np.flatnonzero(
                local_maximum_mask
            )
            + 1
        )

        if candidate_indices.size == 0:
            return []

        # Strongest candidates first.
        sorted_candidates = candidate_indices[
            np.argsort(
                power_db[candidate_indices]
            )[::-1]
        ]

        accepted_indices: list[int] = []

        for candidate_index in sorted_candidates:
            candidate_index = int(
                candidate_index
            )

            is_far_enough = all(
                abs(
                    candidate_index
                    - accepted_index
                )
                >= self._minimum_distance_bins
                for accepted_index in accepted_indices
            )

            if not is_far_enough:
                continue

            accepted_indices.append(
                candidate_index
            )

            if (
                len(accepted_indices)
                >= self._maximum_peaks
            ):
                break

        return [
            SpectrumPeak(
                frequency_hz=float(
                    frequencies_hz[index]
                ),
                power_db=float(
                    power_db[index]
                ),
                bin_index=index,
            )
            for index in accepted_indices
        ]

    def _populate_table(
        self,
        peaks: list[SpectrumPeak],
    ) -> None:
        self._table.setSortingEnabled(
            False
        )

        self._table.setRowCount(
            len(peaks)
        )

        for row, peak in enumerate(
            peaks
        ):
            rank_item = QTableWidgetItem(
                str(row + 1)
            )

            frequency_item = QTableWidgetItem(
                f"{peak.frequency_hz / 1_000_000.0:.6f}"
            )

            power_item = QTableWidgetItem(
                f"{peak.power_db:.2f}"
            )

            bin_item = QTableWidgetItem(
                str(peak.bin_index)
            )

            rank_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            frequency_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            power_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            bin_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self._table.setItem(
                row,
                0,
                rank_item,
            )

            self._table.setItem(
                row,
                1,
                frequency_item,
            )

            self._table.setItem(
                row,
                2,
                power_item,
            )

            self._table.setItem(
                row,
                3,
                bin_item,
            )

        self._table.setSortingEnabled(
            True
        )

        if peaks:
            strongest_peak = peaks[0]

            self._status_label.setText(
                f"Detected {len(peaks)} peaks"
                f"   |   Strongest: "
                f"{strongest_peak.frequency_hz / 1_000_000.0:.6f} MHz"
                f"   |   {strongest_peak.power_db:.2f} dB"
            )
        else:
            self._status_label.setText(
                "No peaks detected."
            )

    def _on_row_double_clicked(
        self,
        row: int,
        column: int,
    ) -> None:
        del column

        if row < 0 or row >= len(
            self._latest_peaks
        ):
            return

        peak = self._latest_peaks[row]

        self.peak_selected.emit(
            peak.frequency_hz,
            peak.power_db,
        )

    def clear(self) -> None:
        self._latest_peaks.clear()
        self._table.setRowCount(0)

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

    @property
    def latest_peaks(
        self,
    ) -> list[SpectrumPeak]:
        return list(
            self._latest_peaks
        )

    @staticmethod
    def _validate_positive_int(
        value: int,
        name: str,
    ) -> int:
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

        return value
