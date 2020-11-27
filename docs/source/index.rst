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
======================

Welcome! This is the documentation for Man-Agent Teaming; Rapid eXperimentation Software (MATRX).

MATRX a 2D-discrete testbed to facilitate Human Agent Teaming (HAT) research. The original use case in MATRX is an urban search and rescue operation in which pairs of a human and an autonomous system have to locate and rescue victims. However, MATRX is very versatile and can, therefore, also be used in many other cases.


Getting started
===============

.. container:: hidden_caption

   .. toctree::
      :caption: Getting started
      :maxdepth: 1

      general_info/aboutmatrx.rst
      installation/installing.rst
      tutorials/tutorials.rst
      tutorials/examples.rst
      reference_by_category.rst


For developers
===============

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: For Developers

   developer_info/how_to_contribute.rst
   developer_info/changelog.rst

.. container:: bullet_list

   * :ref:`How to contribute`
   * :ref:`Changelog`
   * :ref:`genindex`




.. _Reference by Category:
Reference by Category
================================
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
   sections/scenarios.rst
   sections/utils.rst



.. container:: tocdescr

 .. container:: descr

    .. figure:: _static//images/worlds_banner.jpg
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
