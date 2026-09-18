from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
)

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sdr.analysis.spur_analysis import (
    SpurAnalysisResult,
)


class SpurTableWidget(QWidget):
    """
    Display strongest detected spectrum spurs.
    """

    spur_selected = pyqtSignal(
        float,
        float,
    )

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._latest_result: SpurAnalysisResult | None = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Spur Table"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._table = QTableWidget(
            0,
            6,
        )

        self._table.setHorizontalHeaderLabels(
            [
                "#",
                "Frequency [MHz]",
                "Power [dB]",
                "Offset [MHz]",
                "Relative [dBc]",
                "FFT Bin",
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
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self._status_label = QLabel(
            "Waiting for spur analysis..."
        )

        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
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
            self._status_label
        )

    def _connect_signals(self) -> None:
        self._table.cellDoubleClicked.connect(
            self._on_double_clicked
        )

    def update_result(
        self,
        result: SpurAnalysisResult,
    ) -> None:
        if not isinstance(
            result,
            SpurAnalysisResult,
        ):
            raise TypeError(
                "result must be SpurAnalysisResult."
            )

        self._latest_result = result

        self._table.setSortingEnabled(
            False
        )

        self._table.setRowCount(
            len(result.spurs)
        )

        for row, spur in enumerate(
            result.spurs
        ):
            values = (
                str(spur.rank),
                f"{spur.frequency_hz / 1_000_000.0:.6f}",
                f"{spur.power_db:.2f}",
                f"{spur.offset_from_fundamental_hz / 1_000_000.0:+.6f}",
                f"{spur.relative_power_dbc:.2f}",
                str(spur.bin_index),
            )

            for column, text in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    text
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self._table.setItem(
                    row,
                    column,
                    item,
                )

        self._table.setSortingEnabled(
            True
        )

        if result.spurs:
            strongest = result.spurs[0]

            sfdr_db = (
                result.fundamental_power_db
                - strongest.power_db
            )

            self._status_label.setText(
                f"Fundamental: "
                f"{result.fundamental_frequency_hz / 1_000_000.0:.6f} MHz"
                f"   |   Strongest Spur: "
                f"{strongest.frequency_hz / 1_000_000.0:.6f} MHz"
                f"   |   SFDR: "
                f"{sfdr_db:.2f} dB"
                f"   |   Spurs: "
                f"{len(result.spurs)}"
            )
        else:
            self._status_label.setText(
                "No spurs detected."
            )

    def _on_double_clicked(
        self,
        row: int,
        column: int,
    ) -> None:
        del column

        if self._latest_result is None:
            return

        if (
            row < 0
            or row
            >= len(
                self._latest_result.spurs
            )
        ):
            return

        spur = (
            self._latest_result.spurs[
                row
            ]
        )

        self.spur_selected.emit(
            spur.frequency_hz,
            spur.power_db,
        )

    def clear(self) -> None:
        self._latest_result = None
        self._table.setRowCount(0)

        self._status_label.setText(
            "Waiting for spur analysis..."
        )

    @property
    def latest_result(
        self,
    ) -> SpurAnalysisResult | None:
        return self._latest_result
