import os
import inspect
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject, QgsMapLayerType

from .entities.z5_output_data import Z5OutputData
from .dialogs.z5_rankmap_loader_dialog import Z5RankmapLoaderDialog
from .dialogs.z5_performance_curves_dialog import Z5PerformanceCurvesDialog

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

class Zonation5RankmapLoaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.icon = None
        self.load_action = None
        self.context_menu_action = None
        self.load_dialog = None
        self.curves_dialog = None

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

        output_data = Z5OutputData(z5_output_path)
        rankmap_layer.setCustomProperty('Z5_output_data', output_data)
        return True

    def show_load_dialog(self):
        self.load_dialog = Z5RankmapLoaderDialog(
            self.iface,
            self.add_rankmap
        )
        self.load_dialog.show()

    def show_curves_dialog(self):
        active_layer = self.iface.activeLayer()
        if not active_layer.customProperty('Z5_output_data'):
            self.iface.messageBar().pushCritical('Error', 'Layer has no associated performance curves data')
            return
        self.curves_dialog = Z5PerformanceCurvesDialog(self.iface, active_layer.customProperty('Z5_output_data'))
        self.curves_dialog.show()
