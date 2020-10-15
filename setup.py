import os
import shutil
import sys

import setuptools

requires = ['Flask>=1.1.1',
            'jsonpickle',
            'Flask-SocketIO>=3.3.2',
            'numpy>=1.15.4',
            'requests>=2.21.0',
            'colour>=0.1.5',
            'gevent>=1.4.0',
            'flask-cors>=3.0.0',
            'docutils>=0.13.1',
            'Pygments>=2.5.1'
            ],

package_data = {
        "matrx_visualizer": ["mockup/**/*", "templates/**/*", "static/**/*"]
    }

# Load readme file
with open("README.md", "r") as fh:
    long_description = fh.read()

# Load history file
with open("HISTORY.md", "r") as fh:
    history = fh.read()

# Load about file
about_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'matrx',
                          '__version__.py')
about = {}
with open(about_file, 'r') as f:
    exec(f.read(), about)


def load_tokens():
    tokens = {}
    with open("pypi_tokens.txt") as f:
        for line in f:
            name, var = line.partition("=")[::2]
            tokens[name.strip()] = var.rstrip("\n").strip()

    return tokens


def clean_dist():
    folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dist')
    try:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    except FileNotFoundError:
        pass


def build_and_upload(mode):
    print("Loading PyPi private tokens...")
    tokens = load_tokens()
    token = tokens['pypi-test-token'] if mode == 'test' else tokens['pypi-token']
    print("Tokens loaded.\n")

    print("Updating packages...")
    os.system('python -m pip install --user --upgrade setuptools wheel twine')
    print("Packages updated.\n")

    print("Cleaning /dist...")
    clean_dist()
    print("Cleaned /dist.\n")

    print("Building MATRX wheel...")
    os.system('python setup.py sdist bdist_wheel')
    print("Wheel build.\n")

    if mode == 'test':
        print("Uploading to test PyPi servers...")
        cmd_ = 'python -m twine upload --repository-url ' \
               'https://test.pypi.org/legacy/ -u __token__ -p ' + token \
               + ' dist/* '
    else:
        print("Uploading to PyPi servers...")
        cmd_ = 'python -m twine upload --verbose -u __token__ -p ' + token + ' dist/*'
    os.system(cmd_)


# 'setup.py test' shortcut.
if sys.argv[-1] == 'test':
    build_and_upload('test')
    sys.exit()

# 'setup.py deploy' shortcut.
elif sys.argv[-1] == 'deploy':
    build_and_upload('deploy')
    sys.exit()

setuptools.setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about["__url__"],
    packages=setuptools.find_packages(),
    license=about["__license__"],
    install_requires=requires,
    package_data=package_data,
    include_package_data=True,
    classifiers=[   # https://pypi.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
        "Environment :: Web Environment"
    ],
    project_urls={
        'Documentation': about['__doc_url__'],
        'Source': about['__source_url__'],
        'Website': about['__url__']
    },
)
