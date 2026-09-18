from __future__ import annotations

import pyqtgraph as pg

from PyQt6.QtCore import Qt

from sdr.analysis.harmonic_analysis import (
    HarmonicAnalysisResult,
)


class HarmonicMarkerOverlay:
    """
    Draw harmonic markers on an existing PyQtGraph PlotWidget.

    The overlay does not perform harmonic analysis itself.
    It only visualizes a HarmonicAnalysisResult.
    """

    def __init__(
        self,
        plot_widget: pg.PlotWidget,
    ) -> None:
        if plot_widget is None:
            raise ValueError(
                "plot_widget must not be None."
            )

        self._plot_widget = plot_widget

        self._lines: list[pg.InfiniteLine] = []
        self._texts: list[pg.TextItem] = []
        self._points: list[pg.ScatterPlotItem] = []

        self._visible = True
        self._latest_result: HarmonicAnalysisResult | None = None

    def update_result(
        self,
        result: HarmonicAnalysisResult,
    ) -> None:
        if not isinstance(
            result,
            HarmonicAnalysisResult,
        ):
            raise TypeError(
                "result must be a HarmonicAnalysisResult."
            )

        self.clear()

        self._latest_result = result

        for measurement in result.measurements:
            if not measurement.detected:
                continue

            if measurement.measured_frequency_hz is None:
                continue

            if measurement.power_db is None:
                continue

            frequency_mhz = (
                measurement.measured_frequency_hz
                / 1_000_000.0
            )

            power_db = float(
                measurement.power_db
            )

            if measurement.order == 1:
                label = "F"

                relative_text = "0.00 dBc"
            else:
                label = (
                    f"H{measurement.order}"
                )

                if measurement.relative_power_dbc is None:
                    relative_text = "---"
                else:
                    relative_text = (
                        f"{measurement.relative_power_dbc:.2f} dBc"
                    )

            line = pg.InfiniteLine(
                pos=frequency_mhz,
                angle=90,
                movable=False,
                pen=pg.mkPen(
                    width=1.2,
                    style=Qt.PenStyle.DashLine,
                ),
            )

            point = pg.ScatterPlotItem(
                [frequency_mhz],
                [power_db],
                size=11,
                symbol="d",
            )

            text = pg.TextItem(
                text=(
                    f"{label}\n"
                    f"{frequency_mhz:.6f} MHz\n"
                    f"{power_db:.2f} dB\n"
                    f"{relative_text}"
                ),
                anchor=(0.5, 1.15),
            )

            text.setPos(
                frequency_mhz,
                power_db,
            )

            line.setVisible(
                self._visible
            )
            point.setVisible(
                self._visible
            )
            text.setVisible(
                self._visible
            )

            self._plot_widget.addItem(
                line
            )

            self._plot_widget.addItem(
                point
            )

            self._plot_widget.addItem(
                text
            )

            self._lines.append(
                line
            )

            self._points.append(
                point
            )

            self._texts.append(
                text
            )

    def set_visible(
        self,
        visible: bool,
    ) -> None:
        self._visible = bool(
            visible
        )

        for item in (
            self._lines
            + self._points
            + self._texts
        ):
            item.setVisible(
                self._visible
            )

    def clear(self) -> None:
        for line in self._lines:
            self._plot_widget.removeItem(
                line
            )

        for point in self._points:
            self._plot_widget.removeItem(
                point
            )

        for text in self._texts:
            self._plot_widget.removeItem(
                text
            )

        self._lines.clear()
        self._points.clear()
        self._texts.clear()

        self._latest_result = None

    @property
    def marker_count(self) -> int:
        return len(
            self._lines
        )

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def latest_result(
        self,
    ) -> HarmonicAnalysisResult | None:
        return self._latest_result

