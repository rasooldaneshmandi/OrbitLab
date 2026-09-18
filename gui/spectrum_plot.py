import numpy as np

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.figure import Figure


class SpectrumPlot(QWidget):
    """
    Matplotlib-based live SDR spectrum widget.
    """

    def __init__(self):
        super().__init__()

        self.figure = Figure(figsize=(7, 4))
        self.canvas = FigureCanvas(self.figure)

        self.axes = self.figure.add_subplot(111)

        self.axes.set_title("Simulated SDR Spectrum")
        self.axes.set_xlabel("Baseband Frequency [kHz]")
        self.axes.set_ylabel("Relative Power [dB]")
        self.axes.grid(True)

        (self.spectrum_line,) = self.axes.plot([], [])

        self.peak_marker = self.axes.scatter([], [])
        self.peak_text = self.axes.text(
            0.02,
            0.95,
            "",
            transform=self.axes.transAxes,
            verticalalignment="top",
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_spectrum(
        self,
        frequencies_hz,
        power_db,
    ):
        """
        Update spectrum line, peak marker and frequency label.
        """
        frequencies_hz = np.asarray(frequencies_hz)
        power_db = np.asarray(power_db)

        if frequencies_hz.size == 0:
            return

        if power_db.size == 0:
            return

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have equal lengths."
            )

        frequencies_khz = frequencies_hz / 1000.0

        self.spectrum_line.set_data(
            frequencies_khz,
            power_db,
        )

        peak_index = int(np.argmax(power_db))

        peak_frequency_khz = frequencies_khz[
            peak_index
        ]
        peak_power_db = power_db[peak_index]

        self.peak_marker.set_offsets(
            np.array(
                [
                    [
                        peak_frequency_khz,
                        peak_power_db,
                    ]
                ]
            )
        )

        self.peak_text.set_text(
            f"Peak: {peak_frequency_khz:.2f} kHz\n"
            f"Power: {peak_power_db:.2f} dB"
        )

        self.axes.set_xlim(
            frequencies_khz[0],
            frequencies_khz[-1],
        )

        power_min = float(np.min(power_db))
        power_max = float(np.max(power_db))

        power_margin = max(
            5.0,
            0.1 * (power_max - power_min),
        )

        self.axes.set_ylim(
            power_min - power_margin,
            power_max + power_margin,
        )

        self.canvas.draw_idle()