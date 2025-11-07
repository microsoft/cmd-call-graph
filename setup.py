from os import path
from setuptools import setup
import re

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

# Read version from __init__.py using regex to avoid exec()
with open(path.join(this_directory, "callgraph", "__init__.py"), encoding="utf-8") as f:
    version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name="cmd-call-graph",
    packages=["callgraph"],
    entry_points={
        "console_scripts": ["cmd-call-graph = callgraph.callgraph:main"]
    },
    version=version,
    author="Andrea Spadaccini",
    author_email="andrea.spadaccini@gmail.com",
    description="A simple tool to generate a call graph for calls within Windows CMD (batch) files.",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Microsoft/cmd-call-graph",
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Documentation",
    ]
)
