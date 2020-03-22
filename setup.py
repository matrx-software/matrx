import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="matrx",
    version="0.0.93",
    author="The MATRX Development team at TNO.nl",
    author_email="info@matrx-software.com",
    description="A Python package for the rapid development of autonomous systems and human-agent teaming concepts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://matrx-software.com/",
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
    install_requires=['Flask>=1.0.2',
                      'Flask-SocketIO>=3.3.2',
                      'numpy>=1.15.4',
                      'requests>=2.21.0',
                      'colour>=0.1.5',
                      'gevent>=1.4.0',
                      'flask-cors>=3.0.0'
    ],
    package_data={
        "matrx_visualizer": ["mockup/**/*", "templates/**/*", "static/**/*"],
    },
    include_package_data=True,
)
