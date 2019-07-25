import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="matrxs-package-jswaa",
    version="0.0.1",
    author="Jasper van der Waa",
    author_email="jasper.vanderwaa@tno.nl",
    description="A Python package for the rapid development of autonomous systems and human-agent teaming concepts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://ci.tno.nl/gitlab/matrxs/matrxs",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)