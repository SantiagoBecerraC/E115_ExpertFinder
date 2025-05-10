from setuptools import setup, find_packages
# setup file is a marker file for github to deploy as a project

setup(
    name="expert-finder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies are already in requirements-test.txt
    ],
    python_requires=">=3.11",
    description="Expert Finder backend for searching and discovering experts",
    author="Expert Finder Team",
) 