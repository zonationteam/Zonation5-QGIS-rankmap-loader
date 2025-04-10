from .load_rankmap import Zonation5LoaderPlugin

def classFactory(iface):
    return Zonation5LoaderPlugin(iface)
