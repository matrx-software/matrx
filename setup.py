import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="matrxs",
    version="0.0.6",
    author="The MATRXS Development team at TNO.nl",
    author_email="jasper.vanderwaa@tno.nl",
    description="A Python package for the rapid development of autonomous systems and human-agent teaming concepts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://ci.tno.nl/gitlab/matrxs/matrxs",
    packages=setuptools.find_packages(),
    license="MIT License",
    classifiers=[
        "Development Status :: 4 - Beta",  # https://pypi.org/pypi?%3Aaction=list_classifiers
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
        "Environment :: Web Environment"
    ],
)