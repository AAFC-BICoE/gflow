GFlow
========================

This is a CLI application that allows datasets and a workflow to be specified in a config file and then have the workflow executed on an instance of Galaxy.

Installation
------------

Installation right from the source tree (or via pip from PyPI)::

    $ python setup.py install
    
Usage
-----

In the config file, make sure to set the number of datasets required and where they're being imported from (either local, url, or galaxyfs) and include a location and dataset label for each one. For n datasets label the location and label variables as datai and labeli from 0 to n. 

The workflow can be determined from a local file, id (for workflows already imported), or a shared workflow id.

Then, execute the ``gflow`` command as so::

    $ gflow config.txt
