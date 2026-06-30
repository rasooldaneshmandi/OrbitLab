from collections import deque

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class DopplerPlot(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(6, 3))
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111)

        self.values = deque(maxlen=120)
        self.samples = deque(maxlen=120)
        self.counter = 0

        self.line, = self.ax.plot([], [])

        self.ax.set_title("Live Doppler")
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Doppler [kHz]")
        self.ax.grid(True)

    def update_plot(self, doppler_khz: float):
        self.values.append(doppler_khz)
        self.samples.append(self.counter)
        self.counter += 1

        self.line.set_data(list(self.samples), list(self.values))

        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()