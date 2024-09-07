from setuptools import setup, find_packages
from os import path
working_directory = path.abspath(path.dirname(__file__))

setup(
    name="ProgramPigeon_App",
    version="0.0.1",
    author="Mitch Griffith",
    author_email="",
    description="App for coaches to deliver programs to athletes",
    packages=find_packages(),
    install_requires=[],
)