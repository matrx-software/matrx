# Aliasing imports
from matrx.world_builder import WorldBuilder


__docformat__ = "restructuredtext"


######
# We do this so we are sure everything is imported and thus can be found
# noinspection PyUnresolvedReferences
import pkgutil

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
######

# Set package attributes
name = "MATRX: Man-Agent Teaming - Rapid Experimentation Software"
