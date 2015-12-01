GFlow
========================

This is a command line interface application that allows datasets and a workflow to be specified in a config file and then have the workflow executed on an instance of Galaxy.

Installation
------------

Installation right from the source tree (or via pip from PyPI)::

    $ pip install -r requirements.txt
    $ python setup.py install

Configuration
-------------

Make a copy of the sample in ``config/`` and configure the parameters as desired.

Usage
-----

**Environment variables GALAXY_URL and GALAXY_KEY must be set before this application can be used.**

Then, execute the ``gflow`` command:

    $ gflow config/config.yml

Or, if running from the source directory without having installed the application:

    $ ./scripts/gflow config/config.yml
    
Tests
-----

After setting the environment variables mentioned above, execute the tests with:

    $ nosetests
    
A small number of data files and workflow files have been included in ``data/`` and ``workflow/`` for testing purposes.
