from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sdr.analysis.harmonic_analysis import (
    HarmonicAnalysisResult,
    HarmonicMeasurement,
)


class HarmonicTableWidget(QWidget):
    """
    Displays harmonic-analysis results in a table.

    Columns:
        Harmonic
        Expected Frequency
        Measured Frequency
        Power
        Relative Power
        Frequency Error
        Status
    """

    harmonic_selected = pyqtSignal(
        int,
        float,
        float,
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._latest_result: HarmonicAnalysisResult | None = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Harmonic Analysis"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._summary_label = QLabel(
            "Waiting for harmonic analysis..."
        )

        self._summary_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._table = QTableWidget(
            0,
            7,
        )

        self._table.setHorizontalHeaderLabels(
            [
                "Harmonic",
                "Expected [MHz]",
                "Measured [MHz]",
                "Power [dB]",
                "Relative [dBc]",
                "Error [kHz]",
                "Status",
            ]
        )

        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
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

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        layout = QVBoxLayout(self)

        layout.addWidget(
            self._title_label
        )

        layout.addWidget(
            self._table,
            stretch=1,
        )

        layout.addWidget(
            self._summary_label
        )

    def _connect_signals(self) -> None:
        self._table.cellDoubleClicked.connect(
            self._on_cell_double_clicked
        )

    def update_result(
        self,
        result: HarmonicAnalysisResult,
    ) -> None:
        """
        Display a new HarmonicAnalysisResult.
        """
        if not isinstance(
            result,
            HarmonicAnalysisResult,
        ):
            raise TypeError(
                "result must be a HarmonicAnalysisResult."
            )

        self._latest_result = result

        measurements = list(
            result.measurements
        )

        self._table.setSortingEnabled(
            False
        )

        self._table.setRowCount(
            len(measurements)
        )

        detected_count = 0

        for row, measurement in enumerate(
            measurements
        ):
            self._populate_row(
                row,
                measurement,
            )

            if measurement.detected:
                detected_count += 1

        self._table.setSortingEnabled(
            True
        )

        self._summary_label.setText(
            f"Fundamental: "
            f"{result.fundamental_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Power: "
            f"{result.fundamental_power_db:.2f} dB"
            f"   |   Detected harmonics: "
            f"{detected_count}/{len(measurements)}"
        )

    def _populate_row(
        self,
        row: int,
        measurement: HarmonicMeasurement,
    ) -> None:
        if measurement.order == 1:
            harmonic_name = "Fundamental"
        else:
            harmonic_name = (
                f"H{measurement.order}"
            )

        harmonic_item = QTableWidgetItem(
            harmonic_name
        )

        expected_item = QTableWidgetItem(
            f"{measurement.expected_frequency_hz / 1_000_000.0:.6f}"
        )

        if measurement.measured_frequency_hz is None:
            measured_text = "---"
        else:
            measured_text = (
                f"{measurement.measured_frequency_hz / 1_000_000.0:.6f}"
            )

        measured_item = QTableWidgetItem(
            measured_text
        )

        if measurement.power_db is None:
            power_text = "---"
        else:
            power_text = (
                f"{measurement.power_db:.2f}"
            )

        power_item = QTableWidgetItem(
            power_text
        )

        if measurement.relative_power_dbc is None:
            relative_text = "---"
        else:
            relative_text = (
                f"{measurement.relative_power_dbc:.2f}"
            )

        relative_item = QTableWidgetItem(
            relative_text
        )

        if measurement.frequency_error_hz is None:
            error_text = "---"
        else:
            error_text = (
                f"{measurement.frequency_error_hz / 1_000.0:+.3f}"
            )

        error_item = QTableWidgetItem(
            error_text
        )

        status_item = QTableWidgetItem(
            "Detected"
            if measurement.detected
            else "Not detected"
        )

        items = (
            harmonic_item,
            expected_item,
            measured_item,
            power_item,
            relative_item,
            error_item,
            status_item,
        )

        for column, item in enumerate(
            items
        ):
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self._table.setItem(
                row,
                column,
                item,
            )

        # Store the actual measurement order in the first cell.
        harmonic_item.setData(
            Qt.ItemDataRole.UserRole,
            measurement.order,
        )

    def _on_cell_double_clicked(
        self,
        row: int,
        column: int,
    ) -> None:
        del column

        if self._latest_result is None:
            return

        if row < 0:
            return

        measurements = list(
            self._latest_result.measurements
        )

        if row >= len(measurements):
            return

        measurement = measurements[
            row
        ]

        if not measurement.detected:
            return

        if measurement.measured_frequency_hz is None:
            return

        if measurement.power_db is None:
            return

        self.harmonic_selected.emit(
            measurement.order,
            measurement.measured_frequency_hz,
            measurement.power_db,
        )

    def clear(self) -> None:
        self._latest_result = None

        self._table.setRowCount(
            0
        )

        self._summary_label.setText(
            "Waiting for harmonic analysis..."
        )

    @property
    def latest_result(
        self,
    ) -> HarmonicAnalysisResult | None:
        return self._latest_result
