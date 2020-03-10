
# Aliasing imports
from matrx.actions import *
from matrx.agents.capabilities.capability import *
from matrx.logger import *
from matrx.messages.message import Message
from matrx.objects.agent_body import AgentBody
from matrx.objects.env_object import EnvObject
from matrx.objects.standard_objects import *
from matrx.sim_goals import *
from matrx.grid_world import *
from matrx.utils import *
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
