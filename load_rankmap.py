import os
import inspect
from PyQt5.QtWidgets import QAction, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

class Zonation5LoaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

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
            self.dialog = Z5RankmapLoaderDialog(self.iface)
        self.dialog.show()


class Z5RankmapLoaderDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.is_running = False
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
            QgsProject.instance().setCrs(rlayer.crs())
            self.iface.messageBar().pushSuccess('Success', 'Rankmap layer loaded')
            self.z5_output_path = None
            self.open_button.setEnabled(False)
            self.destroy()
        else:
            self.iface.messageBar().pushCritical('Error', 'Invalid rankmap layer')
