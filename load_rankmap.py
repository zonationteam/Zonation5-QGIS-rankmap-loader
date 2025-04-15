import os
import inspect
from PyQt5.QtWidgets import QAction, QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout
from PyQt5.QtGui import QIcon
from qgis.gui import QgsFileWidget
from qgis.core import QgsRasterLayer, QgsProject, QgsMapLayerType

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt, ticker

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

class Z5OutputData:
    def __init__(self, outputfolder_path: str) -> None:
        self.summary_data = None
        self.feature_data = None
        self.set_output_folder(outputfolder_path)

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
        self.icon = None
        self.load_action = None
        self.context_menu_action = None
        self.dialog = None
        self.layers = {}

    def initGui(self):
        self.icon = QIcon(os.path.join(os.path.join(cmd_folder, 'icon.ico')))

        self.load_action = QAction(self.icon, 'Load Zonation 5 Rankmap', self.iface.mainWindow())
        self.iface.addToolBarIcon(self.load_action)
        self.load_action.triggered.connect(self.show_load_dialog)

        self.context_menu_action = QAction(self.icon, 'Show performance curves')
        self.iface.addCustomActionForLayerType(
            self.context_menu_action,
            'Zonation 5',
            QgsMapLayerType.RasterLayer,
            allLayers=True
        )

    def unload(self):
        self.iface.removeToolBarIcon(self.load_action)
        self.iface.removeCustomActionForLayerType(self.context_menu_action)
        del self.load_action

    def add_rankmap(self, z5_output_path, rankmap_name_extension) -> bool:
        rlayer_name = 'rankmap'
        if rankmap_name_extension != '':
            rlayer_name = f'{rlayer_name}_{rankmap_name_extension}'
        rankmap = QgsRasterLayer(f'{z5_output_path}/rankmap.tif', rlayer_name)
        if not rankmap.isValid():
            return False
        rankmap_layer = QgsProject.instance().addMapLayer(rankmap)
        self.iface.addCustomActionForLayer(
            QAction(self.icon, 'Show performance curves'),
            rankmap_layer
        )
        self.context_menu_action.triggered.connect(self.show_curves_dialog)
        rankmap_layer.destroyed.connect(lambda: self.on_rankmap_destroyed(rankmap_layer))

        output_data = Z5OutputData(z5_output_path)

        self.layers[rankmap_layer.id] = output_data
        return True

    def on_rankmap_destroyed(self, rankmap_layer):
        self.layers.pop(rankmap_layer.id)

    def show_load_dialog(self):
        self.dialog = Z5RankmapLoaderDialog(
            self.iface,
            self.add_rankmap,
            self.on_rankmap_destroyed
        )
        self.dialog.show()

    def show_curves_dialog(self):
        active_layer = self.iface.activeLayer()
        if active_layer.id not in self.layers:
            self.iface.messageBar().pushCritical('Error', 'Layer has no associated performance curves data')
            return
        self.dialog.destroy()
        self.dialog = Z5PerformanceCurvesDialog(self.iface, self.layers[active_layer.id])
        self.dialog.show()

class Z5RankmapLoaderDialog(QDialog):
    def __init__(self, iface, add_rankmap, on_rankmap_destroyed):
        super().__init__()
        self.iface = iface
        self.add_rankmap = add_rankmap
        self.on_rankmap_destroyed = on_rankmap_destroyed
        self.folder_widget = QgsFileWidget()
        self.name_extension_field = QLineEdit()
        self.open_button = QPushButton('Open')
        self.z5_output_path = None

        self.setMinimumSize(600, 120)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Load Zonation 5 Rankmap')

        layout = QFormLayout()

        layout.addRow(QLabel("Add Zonation 5 output rankmap as a layer."))

        self.folder_widget.setDialogTitle('Open Zonation 5 output folder')
        self.folder_widget.setStorageMode(QgsFileWidget.StorageMode.GetDirectory)
        self.folder_widget.fileChanged.connect(self._on_output_folder_selection_changes)
        layout.addRow(
            QLabel('Zonation output folder path:'),
            self.folder_widget
        )

        layout.addRow(
            QLabel('Rankmap name extension (optional):'),
            self.name_extension_field
        )

        if self.z5_output_path is None:
            self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.run)
        layout.addRow(self.open_button)

        self.setLayout(layout)

    def _on_output_folder_selection_changes(self):
        self.z5_output_path = self.folder_widget.filePath()
        self.open_button.setEnabled(True)

    def run(self):
        rankmap_name_extension = self.name_extension_field.text()
        if self.add_rankmap(self.z5_output_path, rankmap_name_extension):
            self.z5_output_path = None
            self.name_extension_field.clear()
            self.open_button.setEnabled(False)
            self.destroy()
            self.iface.messageBar().pushSuccess('Success', 'Rankmap layer loaded')
        else:
            self.iface.messageBar().pushCritical('Error', 'Invalid rankmap layer')


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
