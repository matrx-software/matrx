.. MATRXS documentation master file, created by
   sphinx-quickstart on Fri Jul 26 09:03:28 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   https://raw.githubusercontent.com/tobiasHeinke/Blender-Manual/master/blender_docs/resources/theme/css/theme_overrides.css
.. only:: builder_html

   .. |vertical_separator| unicode:: U+02758

.. figure:: /_static/images/tno_banner.png
   :width: 150%

MATRXS' documentation
======================

Welcome! This is the documentation for Man-Agent Teaming; Rapid eXperimentation Software (MATRXS).

MATRXS a 2D-discrete testbed to facilitate Human Agent Teaming (HAT) research. The original use case in MATRXS is an urban search and rescue operation in which pairs of a human and an autonomous system have to locate and rescue victims. However, MATRXS is very versatile and can, therefore, also be used in many other cases.


Getting started
===============

+---------------------+---------------------+---------------------+---------------------+
| :ref:`About MATRXS` | :ref:`Installation` |  :ref:`Reference`   |  :ref:`genindex`    |
+---------------------+---------------------+---------------------+---------------------+
| :ref:`Tutorials`    |  :ref:`F.A.Q.`      |  :ref:`search`      |  :ref:`modindex`    |
+---------------------+---------------------+---------------------+---------------------+


.. toctree::
   :maxdepth: 2
   :caption: Getting started
   :hidden:

   about/aboutmatrxs.rst
   installation/installing.rst
   about/tutorials.rst
   about/FAQ.rst





Sections
========
.. The image ratio is: width: 350px; height: 350/4 + (2x5) ~= 98px
.. toctree::
   :maxdepth: 2
   :caption: Sections
   :hidden:

   sections/worlds.rst
   sections/actions.rst
   sections/brains.rst
   sections/objects.rst
   sections/simgoals.rst
   sections/utils.rst
..   sections/visuals.rst


.. .. only:: builder_html and (not singlehtml)

.. container:: tocdescr

  .. container:: descr

     .. figure:: /_static/images/worlds_banner.jpg
        :target: sections/worlds.html

     :ref:`Worlds`
        Learn MATRXS' way of creating worlds.

  .. container:: descr

     .. figure:: /_static/images/brains_banner.jpg
        :target: sections/brains.html

     :ref:`Brains`
       Check this section for a piece of the agents' minds.

  .. container:: descr

     .. figure:: /_static/images/shape_banner.jpg
        :target: sections/objects.html

     :ref:`Object placement`
        Make the world more worldlike by placing objects in it.

  .. container:: descr

     .. figure:: /_static/images/action_banner.jpg
        :target: sections/actions.html

     :ref:`Actions`
        Agents can perform actions.

  .. container:: descr

     .. figure:: /_static/images/goal_banner.jpg
        :target: sections/simgoals.html

     :ref:`Simulation goals`
        A certain goal is set for the simulation to end.

  .. container:: descr

     .. figure:: /_static/images/utils_banner.jpg
        :target: sections/utils.html

     :ref:`Utils`
        Useful functions.

..      .. container:: descr

..         .. figure:: /_static/images/server.jpg
            :target: sections/visuals.html
           :ref:`Visualization`
            Visualization by using a Flask server.



Resources
=========
* `TNO <https://tno.nl>`_

.. Indices and tables
   ==================
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`















