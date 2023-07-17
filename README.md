# The MATRX Software

[![DOI](https://zenodo.org/badge/243515218.svg)](https://zenodo.org/badge/latestdoi/243515218)

## Human-Agent Teaming Rapid Experimentation Software

The field of human-agent teaming (HAT) research aims to improve the collaboration between humans and intelligent agents. Small tasks are often designed to do research in agent development and perform evaluations with human experiments. Currently there is no dedicated library of such tasks. Current tasks are build and maintained independent of each other, making it difficult to benchmark research or explore research to different type of tasks.

<img src="https://www.matrx-software.com/wp-content/uploads/2020/02/matrx_logo.svg" height="100">

To remedy the lack of a team task library for HAT research, we developed the Human-Agent Teaming Rapid Experimentation Software package, or MATRX for short. MATRX’s main purpose is to provide a suite of team tasks with one or multiple properties important to HAT research (e.g. varying team size, decision speed or inter-team dependencies). In addition to these premade tasks, MATRX facilitates the rapid development of new team tasks. 

Also, MATRX supports HAT solutions to be implemented in the form of [Team Design Patterns](https://s3.amazonaws.com/academia.edu.documents/61212125/TeamPatterns_CR_v520191114-20876-1u5752p.pdf?response-content-disposition=inline%3B%20filename%3DTeam_Design_Patterns.pdf&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWOWYYGZ2Y53UL3A%2F20200221%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20200221T092845Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=6188328a97b458647775b65c0b0669c0b56e44f707d49e7398dcf40849181a6e) (TDP). This allows for the creation of a TDP library which structures HAT research by mapping task properties, solutions and obtained results in such a way that identifies research gaps. Perhaps more importantly, it allows for system designers to search for a concrete and evaluated solution to their issues related to HAT.

This all is made possible by MATRX. 

Feel free to try some tasks or to browse our official [webpage](https://matrx-software.com/). This also includes a set of elaborate [tutorials](https://matrx-software.com/tutorials/), [documentation](http://docs.matrx-software.com/en/latest/) and [contribution guide](https://matrx-software.com/contribution_guide/).
.

## Citation
If you use this software in your work, consider citing it as follows:

  _van der Waa, J.S & Haije, T (2023). MATRX: Human Agent Teaming Rapid Experimentation software. Zenodo._

    @software{matrx_2023,
    author       = {Jasper van der Waa, Tjalling Haije},
    title        = {MATRX: Human Agent Teaming Rapid Experimentation software},
    month        = {July},
    year         = {2023},
    publisher    = {Zenodo},
    version      = {2.3.2},
    doi          = {10.5281/zenodo.8154912},
    url          = {https://doi.org/10.5281/zenodo.8154912}}
