from setuptools import setup, find_packages
import pathlib

current_dir = pathlib.Path(__file__).parent.resolve()
long_description = (current_dir / 'README.md').read_text(encoding='utf-8')

setup(
    name="CENSAr",
    version="0.1dev0",
    description='Templates for census analysis',
    long_description=long_description,
    author='CEEU - UNSAM',
    author_email='fcatalano@unsam.edu.ar',
    url='https://github.com/CEEU-lab/CENSAr',
    classifiers=[
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10'
    ],
    packages=find_packages(exclude=['*.tests']),
    install_requires=[
        'numpy >= 1.22.2',
        'pandas >= 1.4.1',
        'streamlit >= 1.2',
        'matplotlib >= 3.4.3',
    ]
)
