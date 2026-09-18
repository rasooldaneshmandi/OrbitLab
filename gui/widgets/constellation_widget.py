from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class ConstellationWidget(QWidget):
    """
    Real-time IQ constellation display.

    The real component is shown on the I axis.
    The imaginary component is shown on the Q axis.
    """

    def __init__(
        self,
        *,
        maximum_points: int = 4000,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if maximum_points <= 0:
            raise ValueError(
                "maximum_points must be greater than zero."
            )

        self._maximum_points = int(
            maximum_points
        )

        self._latest_iq: np.ndarray | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "IQ Constellation"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._point_count_spin = QSpinBox()
        self._point_count_spin.setRange(
            100,
            100_000,
        )
        self._point_count_spin.setValue(
            self._maximum_points
        )

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(
            QLabel("Displayed points:")
        )

        controls_layout.addWidget(
            self._point_count_spin
        )

        controls_layout.addStretch(1)

        self._plot_widget = pg.PlotWidget()

        self._plot_widget.setLabel(
            "bottom",
            "In-phase",
            units="I",
        )

        self._plot_widget.setLabel(
            "left",
            "Quadrature",
            units="Q",
        )

        self._plot_widget.showGrid(
            x=True,
            y=True,
            alpha=0.25,
        )

        self._plot_widget.setAspectLocked(
            True
        )

        self._scatter = pg.ScatterPlotItem(
            size=5,
            symbol="o",
            pxMode=True,
        )

        self._plot_widget.addItem(
            self._scatter
        )

        # I = 0
        self._vertical_axis = pg.InfiniteLine(
            pos=0.0,
            angle=90,
            movable=False,
        )

        # Q = 0
        self._horizontal_axis = pg.InfiniteLine(
            pos=0.0,
            angle=0,
            movable=False,
        )

        self._plot_widget.addItem(
            self._vertical_axis
        )

        self._plot_widget.addItem(
            self._horizontal_axis
        )

        self._status_label = QLabel(
            "Waiting for IQ samples..."
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
            self._plot_widget,
            stretch=1,
        )

        layout.addWidget(
            self._status_label
        )

    def update_iq(
        self,
        iq_samples: np.ndarray,
    ) -> None:
        iq_samples = np.asarray(
            iq_samples,
            dtype=np.complex64,
        )

        if iq_samples.ndim != 1:
            raise ValueError(
                "iq_samples must be one-dimensional."
            )

        if iq_samples.size == 0:
            self.clear()
            return

        if not np.all(
            np.isfinite(iq_samples.real)
        ):
            raise ValueError(
                "IQ real component contains invalid values."
            )

        if not np.all(
            np.isfinite(iq_samples.imag)
        ):
            raise ValueError(
                "IQ imaginary component contains invalid values."
            )

        self._latest_iq = (
            iq_samples.copy()
        )

        requested_points = int(
            self._point_count_spin.value()
        )

        number_of_points = min(
            requested_points,
            iq_samples.size,
        )

        if number_of_points <= 0:
            return

        displayed_iq = iq_samples[
            -number_of_points:
        ]

        i_values = np.real(
            displayed_iq
        )

        q_values = np.imag(
            displayed_iq
        )

        self._scatter.setData(
            i_values,
            q_values,
        )

        mean_i = float(
            np.mean(i_values)
        )

        mean_q = float(
            np.mean(q_values)
        )

        rms_magnitude = float(
            np.sqrt(
                np.mean(
                    np.abs(displayed_iq) ** 2
                )
            )
        )

        peak_magnitude = float(
            np.max(
                np.abs(displayed_iq)
            )
        )

        self._status_label.setText(
            f"Samples: {number_of_points}"
            f"   |   Mean I: {mean_i:+.4f}"
            f"   |   Mean Q: {mean_q:+.4f}"
            f"   |   RMS: {rms_magnitude:.4f}"
            f"   |   Peak: {peak_magnitude:.4f}"
        )

    def clear(self) -> None:
        self._latest_iq = None

        self._scatter.setData(
            [],
            [],
        )

        self._status_label.setText(
            "Waiting for IQ samples..."
        )

    @property
    def latest_iq(
        self,
    ) -> np.ndarray | None:
        if self._latest_iq is None:
            return None

        return self._latest_iq.copy()
