from setuptools import setup


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

setup(
    name = "GFlow",
    packages = ["gflow"],
    scripts = ["scripts/gflow"],
    version = "0.1.0",
    description = "Command line tool for running Galaxy workflows.",
    long_description = long_descr,
    author = "Alex MacLean",
    author_email = "maclean199@gmail.com",
    url = "https://github.com/AAFC-MBB/gflow",
)
