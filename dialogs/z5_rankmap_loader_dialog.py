from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QFormLayout
from qgis.gui import QgsFileWidget

class Z5RankmapLoaderDialog(QDialog):
    def __init__(self, iface, add_rankmap):
        super().__init__()
        self.iface = iface
        self.add_rankmap = add_rankmap
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

