from PyQt5.QtWidgets import QDialog, QVBoxLayout

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt, ticker

from ..entities.z5_output_data import Z5OutputData

class Z5PerformanceCurvesDialog(QDialog):
    def __init__(self, iface, output_data: Z5OutputData):
        super().__init__()
        self.iface = iface
        self.output_data = output_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Performance curves')

        layout = QVBoxLayout()

        curves_figure_canvas = plt.Figure(figsize=(8,6), dpi=100)
        ax_curves = curves_figure_canvas.add_subplot(111)
        feature_line, *_ = ax_curves.plot(
            self.output_data.feature_data['rank'],
            self.output_data.feature_data.iloc[:, 1:],
            color='lightblue',
            label='Feature curves'
        )
        summary_line, = ax_curves.plot(
            self.output_data.summary_data['rank'],
            self.output_data.summary_data['mean'],
            color='blue',
            label='Summary curve, mean'
        )
        ax_curves.legend(handles=[summary_line, feature_line])
        ax_curves.grid(True, alpha=0.3)
        ax_curves.set_xlabel('Priority rank')
        ax_curves.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
        ax_curves.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))
        ax_curves.set_ylabel('Coverage of features')
        ax_curves.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
        ax_curves.yaxis.set_minor_locator(ticker.MultipleLocator(0.05))
        ax_curves.set_title('Performance curves')

        curves_area = FigureCanvas(curves_figure_canvas)
        layout.addWidget(curves_area)

        self.setLayout(layout)
