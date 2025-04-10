import os
import inspect
from PyQt5.QtWidgets import QAction, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt, ticker

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

class DataService:
    def __init__(self) -> None:
        self.summary_data = None
        self.feature_data = None

    def __str__(self) -> str:
        sum_data_line = f"Summary data:\n{str(self.summary_data.head(2))}"
        feat_data_line = f"Feature data:\n{str(self.feature_data.head(2))}"
        return f"{sum_data_line},\n{feat_data_line}\n"

    def set_output_folder(self, outputfolder_path: str) -> None:
        self.summary_data = pd.read_csv(
            f"{outputfolder_path}/summary_curves.csv",
            sep=' '
        )
        self.feature_data = pd.read_csv(
            f"{outputfolder_path}/feature_curves.csv",
            sep=' '
        ).iloc[:, :-1] # Because this file contains whitespaces at the end of each row


class Zonation5LoaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
        self.data_service = DataService()

    def initGui(self):
        icon = os.path.join(os.path.join(cmd_folder, 'icon.ico'))
        self.action = QAction(QIcon(icon), 'Load Zonation 5 Rankmap', self.iface.mainWindow())
        self.iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.show_dialog)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def show_dialog(self):
        if not self.dialog:
            self.dialog = Z5RankmapLoaderDialog(self.iface, self.data_service)
        elif (self.data_service.feature_data is not None) & (self.data_service.summary_data is not None):
            self.dialog = Z5PerformanceCurvesDialog(self.iface, self.data_service)
        self.dialog.show()


class Z5RankmapLoaderDialog(QDialog):
    def __init__(self, iface, data_service):
        super().__init__()
        self.iface = iface
        self.data_service = data_service
        self.z5_output_path = None
        self.open_button = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Load Zonation 5 Rankmap')

        layout = QVBoxLayout()
        intro_label = QLabel("This plugin adds Zonation 5 output rankmap as a layer and show associated performance curves in QGIS.")
        layout.addWidget(intro_label)

        layout.addWidget(QLabel('Zonation output folder path:'))
        fdialog_button = QPushButton('Select Zonation output folder')
        fdialog_button.clicked.connect(self._on_output_folder_selection_clicked)
        layout.addWidget(fdialog_button)

        self.open_button = QPushButton('Open')
        if self.z5_output_path is None:
            self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.run)
        layout.addWidget(self.open_button)

        self.setLayout(layout)

    def _on_output_folder_selection_clicked(self) -> None:
        output_folder_path = QFileDialog.getExistingDirectory(
            self, 'Open folder'
        )
        self.z5_output_path = output_folder_path
        self.open_button.setEnabled(True)

    def run(self):
        rankmap_path = f'{self.z5_output_path}/rankmap.tif'
        rlayer = QgsRasterLayer(rankmap_path, 'rankmap')
        if rlayer.isValid():
            QgsProject.instance().addMapLayer(rlayer)
            self.data_service.set_output_folder(self.z5_output_path)
            self.iface.messageBar().pushSuccess('Success', 'Rankmap layer loaded')
            self.z5_output_path = None
            self.open_button.setEnabled(False)
            self.destroy()
            self = Z5PerformanceCurvesDialog(self.iface, self.data_service)
        else:
            self.iface.messageBar().pushCritical('Error', 'Invalid rankmap layer')


class Z5PerformanceCurvesDialog(QDialog):
    def __init__(self, iface, data_service):
        super().__init__()
        self.iface = iface
        self.data_service = data_service
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Performance curves')

        layout = QVBoxLayout()

        curves_figure_canvas = plt.Figure(figsize=(8,6), dpi=100)
        ax_curves = curves_figure_canvas.add_subplot(111)
        feature_line, *_ = ax_curves.plot(
            self.data_service.feature_data['rank'],
            self.data_service.feature_data.iloc[:, 1:],
            color='lightblue',
            label='Feature curves'
        )
        summary_line, = ax_curves.plot(
            self.data_service.summary_data['rank'],
            self.data_service.summary_data['mean'],
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
