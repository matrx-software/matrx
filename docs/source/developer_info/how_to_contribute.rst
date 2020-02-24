.. _How to contribute:

########################
How to contribute
########################



--------------------
Documentation
--------------------
| **What docstring format does MATRX use?**
| MATRX uses the `Numpy docstring format <https://numpydoc.readthedocs.io/en/latest/format.html>`_.


| **How can I change the default docstring format in PyCharm?**
| Open the settings, and go to Tools > Python Integrated Tools > NumPy.

| **How can I generate the Readthedocs documentation locally to test my documentation changes?**
| Make sure you have all dependencies from requirements.txt installed.
| Go to the MATRX/docs folder in a terminal
| Type: make html
| Open: MATRX/docs/build/html/index.html in your browser

| **I added a function / class (e.g. new agent type), but it does not show on readthedocs, what do I do?**
| The documentation generation on readthedocs is semi-automatic. New classes might have to be added manually.
| To add a new class to be mined by readthedocs, in MATRX go to the folder /docs/source/sections.
| Open the file that matches your category, e.g. for a new agent that is /docs/source/sections/agents.rst.
| Add your new class to the list in similar fashion as the other already present classes.
| Check if your changes worked as you expected locally before pushing (see the question above).
| Push your changes and create a merge request for your branch to dev, after which matrx.readthedocs.io will be automatically updated with your changes.
