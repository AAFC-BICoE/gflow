# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('gflow/gflow.py').read(),
    re.M
    ).group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "gflow",
    packages = ["gflow"],
    entry_points = {
        "console_scripts": ['gflow = gflow.gflow:main']
        },
    version = version,
    description = "Command line tool for running Galaxy workflows.",
    long_description = long_descr,
    author = "Alex MacLean",
    author_email = "maclean199@gmail.com",
    url = "https://github.com/AAFC-MBB/gflow",
    )
