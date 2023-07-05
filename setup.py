import pathlib

from setuptools import setup, find_packages

current_dir = pathlib.Path(__file__).parent.resolve()
long_description = (current_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="CENSAr",
    version="0.1.0",
    description="Templates for spatial statistics analysis",
    long_description=long_description,
    author="CEEU - UNSAM",
    author_email="fcatalano@unsam.edu.ar",
    url="https://github.com/CEEU-lab/CENSAr",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(exclude=["*.tests"]),
    install_requires=[
        "scikit-learn == 1.2.2",
        "numpy >= 1.22.2",
        "pandas >= 1.4.1",
        "matplotlib >= 3.4.3",
        "seaborn == 0.12.2",
        "geopandas == 0.13.0",
        "mapclassify == 2.5.0",
        "rtree == 1.0.1"],
)
