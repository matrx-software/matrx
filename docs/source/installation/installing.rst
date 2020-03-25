.. _Installation:

####################################
Installation and first run
####################################

Installing MATRX
========================

MATRX runs on Python 3.6 or higher.

Obtaining the latest MATRX release:
The latest release of MATRX can be found on the `Github page:<https://github.com/matrx/MATRX>`_).
Download or clone the file structure to your workspace.

Installing dependencies:
The 3rd-party packages required to run MATRX are defined in ``requirements.txt``.
Using ``PIP``::

    pip3 install -r requirements.txt

Using ``Conda``::

    conda install --file requirements.txt

First run
========================
From the MATRX workspace location, start the testbed mainloop and visualization server::
python3 main.py

Open a web browser and visit the MATRX' god view visualization by opening the following link::
`<http://localhost:3000/god>`_

Other views, such as the ``agent view`` and ``human-agent view`` can be opened via the start page, accessable from::
`<http://localhost:3000/>`_

Please follow the :ref:`Tutorials` to familiarize yourself with the fundamentals of MATRX.
