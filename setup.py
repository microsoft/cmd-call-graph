from setuptools import setup

with open("README.md", "rb") as readme:
    long_description = readme.read().decode("utf-8")

setup(
    name="cmd-call-graph",
    packages=["callgraph"],
    entry_points={
        "console_scripts": ["cmd-call-graph = callgraph.callgraph:main"]
    },
    version=0.2,
    author="Andrea Spadaccini",
    author_email="andrea.spadaccini@gmail.com",
    description="A simple tool to generate a call graph for calls within Windows CMD (batch) files.",
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
