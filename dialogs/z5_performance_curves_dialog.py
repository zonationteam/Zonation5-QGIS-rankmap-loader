from PyQt5.QtWidgets import QDialog, QVBoxLayout

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt, ticker

class Z5PerformanceCurvesDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.layout = None
        self.curves_figure_canvas = None
        self.ax_curves = None
        self.rankmap_layer = None
        self.init_ui()

    def init_ui(self):
        self.iface.currentLayerChanged.connect(self.draw_plot_area)
        self.layout = QVBoxLayout()
        self.draw_plot_area()

    def draw_plot_area(self):
        self.rankmap_layer = self.iface.activeLayer()
        if not self.rankmap_layer:
            self.done(0)
            return
        if self.layout:
            self.layout.removeItem(self.layout.itemAt(0))
        self.curves_figure_canvas = plt.Figure(figsize=(8,6), dpi=100)
        self.ax_curves = self.curves_figure_canvas.add_subplot(111)

        if not self.rankmap_layer.customProperty('Z5_output_data'):
            self.draw_empty()
        else:
            self.draw_curves()

        curves_area = FigureCanvas(self.curves_figure_canvas)
        self.layout.addWidget(curves_area)
        self.setLayout(self.layout)

    def draw_empty(self):
        self.ax_curves.set_title(f'No Zonation 5 output data for {self.rankmap_layer.name()}')

    def draw_curves(self):
        title = f'Performance curves, {self.rankmap_layer.name()}'
        output_data = self.rankmap_layer.customProperty('Z5_output_data')
        self.setWindowTitle(title)

        feature_line, *_ = self.ax_curves.plot(
            output_data.feature_data['rank'],
            output_data.feature_data.iloc[:, 1:],
            color='lightblue',
            label='Feature curves'
        )
        summary_line, = self.ax_curves.plot(
            output_data.summary_data['rank'],
            output_data.summary_data['mean'],
            color='blue',
            label='Summary curve, mean'
        )
        self.ax_curves.legend(handles=[summary_line, feature_line])
        self.ax_curves.grid(True, alpha=0.3)
        self.ax_curves.set_xlabel('Priority rank')
        self.ax_curves.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
        self.ax_curves.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))
        self.ax_curves.set_ylabel('Coverage of features')
        self.ax_curves.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
        self.ax_curves.yaxis.set_minor_locator(ticker.MultipleLocator(0.05))
        self.ax_curves.set_title(title)
