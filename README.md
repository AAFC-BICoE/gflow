GFlow
========================

This is a command line interface application that allows datasets and a workflow to be specified in a config file and then have the workflow executed on an instance of Galaxy.

Installation
------------

Installation right from the source tree:

    $ pip install -r requirements.txt
    $ pip install .

Configuration
-------------

Make a copy of the sample file in ``config/`` and configure the parameters in it as desired:

    $ cp config/config.yml.sample config/config.yml

Usage
-----

Then, execute the ``gflow`` command:

    $ gflow config/config.yml

Or, if running from the source directory without having installed the application:

    $ export PYTHONPATH=$PYTHONPATH:$PWD
    $ ./scripts/gflow config/config.yml
    
Tests
-----

A small number of data files and workflow files have been included in ``data/`` and ``workflow/`` for testing purposes.
Execute the tests with:

    $ py.test tests
    
Run the tests without the need to install any requirements:

    $ python setup.py test

Generate a code coverage report:

    $ py.test --cov gflow
