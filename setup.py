from os import path
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="cmd-call-graph",
    packages=["callgraph"],
    entry_points={
        "console_scripts": ["cmd-call-graph = callgraph.callgraph:main"]
    },
    version="1.2.0",
    author="Andrea Spadaccini",
    author_email="andrea.spadaccini@gmail.com",
    description="A simple tool to generate a call graph for calls within Windows CMD (batch) files.",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Microsoft/cmd-call-graph",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Documentation",
    ]
)
