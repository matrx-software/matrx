__docformat__ = "restructuredtext"

######
# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("numpy", "Flask", "Flask-SocketIO", "eventlet", "noise", "shapely", "colour", "requests")
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append("{0}: {1}".format(dependency, str(e)))

if missing_dependencies:
    raise ImportError(
        "Unable to import required dependencies:\n" + "\n".join(missing_dependencies)
    )
del hard_dependencies, dependency, missing_dependencies

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
name = "MATRXS: Man-Agent Teaming - Rapid Experimentation Software"
