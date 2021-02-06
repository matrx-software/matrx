.. MATRX documentation master file, created by
   sphinx-quickstart on Fri Jul 26 09:03:28 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   https://raw.githubusercontent.com/tobiasHeinke/Blender-Manual/master/blender_docs/resources/theme/css/theme_overrides.css
.. only:: builder_html

   .. |vertical_separator| unicode:: U+02758

.. figure:: _static/images/tno_banner.png
   :width: 150%

MATRX documentation
======================================

Welcome! This is the class and function reference documentation for the huMan-Agent Teaming; Rapid eXperimentation Software (MATRX).

After having installed MATRX (|matrx_install_guide|) and having tried out one or more tutorials (see the tutorials on the |matrx_tutorials|), additional information can be found here on specific classes, functions and parameters that are not described in a tutorial.

.. |matrx_install_guide| raw:: html

    <a href="https://matrx-software.com/docs/tutorials/basics/installation/" target="_blank">see installing MATRX</a>

.. |matrx_tutorials| raw:: html

    <a href="https://matrx-software.com/tutorials/" target="_blank">MATRX website</a>

.. _Reference by Category:

Reference by Category
================================================================
.. The image ratio is: width: 350px; height: 350/4 + (2x5) ~= 98px
.. toctree::
   :maxdepth: 2
   :caption: Reference by Category
   :hidden:

   sections/worlds.rst
   sections/actions.rst
   sections/agents.rst
   sections/objects.rst
   sections/simgoals.rst
   sections/api.rst
   sections/cases.rst
   sections/logging.rst
   sections/messages.rst



.. container:: tocdescr

 .. container:: descr

    .. figure:: _static/images/worlds_banner.jpg
       :target: sections/worlds.html

    :ref:`Worlds`
       Learn MATRX' way of creating worlds.

 .. container:: descr

    .. figure:: _static/images/brains_banner.jpg
       :target: sections/agents.html

    :ref:`Agents`
      Check this section for a piece of the agents' minds.

 .. container:: descr

    .. figure:: _static/images/shape_banner.jpg
       :target: sections/objects.html

    :ref:`Objects`
       Make the world more worldlike by placing objects in it.

 .. container:: descr

    .. figure:: _static/images/action_banner.jpg
       :target: sections/actions.html

    :ref:`Actions`
       Agents can perform actions.

 .. container:: descr

    .. figure:: _static/images/goal_banner.jpg
       :target: sections/simgoals.html

    :ref:`Goals`
       Goals can be specified that track progress and determine when the simulation should end.

 .. container:: descr

    .. figure:: _static/images/shape_banner.jpg
       :target: sections/cases.html

    :ref:`Cases`
       Defining a world containing objects, agents, actions, and simulation goals.

 .. container:: descr

    .. figure:: _static/images/utils_banner.jpg
       :target: sections/api.html

    :ref:`API`
       Connecting MATRX to other software, such as GUIs or frameworks.

 .. container:: descr

    .. figure:: _static/images/action_banner.jpg
       :target: sections/messages.html

    :ref:`Messages`
       Communication between agents via messages.

 .. container:: descr

    .. figure:: _static/images/utils_banner.jpg
       :target: sections/logging.html

    :ref:`Logging`
       Logging of results during an simulation.
