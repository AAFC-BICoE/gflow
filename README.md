GFlow
========================

This is a command line interface application that allows datasets and a workflow to be specified in a config file and then have the workflow executed on an instance of Galaxy.

Installation
------------

From the source directory:

    $ pip install -r requirements.txt
    $ python setup.py install 

Configuration
-------------

Make a copy of the sample config file in ``config/`` and set the parameters in it as desired:

    $ cp config/config.yml.sample config/config.yml

Usage
-----

Then, execute:

    $ gflow config/config.yml

Or, if executing from the source directory without having installed the tool:

    $ export PYTHONPATH=$PYTHONPATH:$PWD
    $ ./scripts/gflow config/config.yml
    
Tests
-----

A small number of data files and workflow files have been included in ``data/`` and ``workflow/`` for testing purposes.
After setting the ```GALAXY_URL``` and ```GALAXY_API_KEY``` environment variables, execute the tests with:

    $ python setup.py test
