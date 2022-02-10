import pathlib
import setuptools
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="ipranger",
    version="1.1.1",
    description="A python package and commandline tool for generating IPv4-addresses based on a schema.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/bytebutcher/ipranger",
    author="bytebutcher",
    author_email="thomas.engel.web@gmail.com",
    license="GPL-3.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'dacite==1.6.0',
        'parameterized==0.8.1',
        'pyparsing==3.0.6'
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "ipranger=ipranger:main",
        ]
    },
)
