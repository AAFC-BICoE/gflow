GFlow
========================

This is a command line interface application that allows datasets and a workflow to be specified in a config file and then have the workflow executed on an instance of Galaxy.

Installation
------------

Installation right from the source tree (or via pip from PyPI)::

    $ pip install -r requirements.txt
    $ python setup.py install

Config File
-----------

An example config file has been included in ``config/``. Copy it and set the options to what you require.

``[library]``

``library`` - The name of the library that will be created

``[input]``

``datatset_src`` - Where the datasets will be imported from, one of ``local``, ``url``, or ``galaxyfs``

``num_datasets`` - The number of datasets to be imported

``data_[0..n]`` - The dataset locations for 0 to n datasets

``label_[0..n]`` - The dataset labels for 0 to n datasets

``[output]``

``output_history_name`` - The name of the history that will be created

``[workflow]``

``source`` - Where the workflow is being imported from, one of ``local``, ``id``, or ``shared``

``workflow`` - A file location if importing from ``local`` or an id if using ``id`` or ``shared`` as a source

``[tool_params]``

``num_tools`` - The number of tools in the workflow that require runtime parameters

``tool_[0..m]`` - The id of a tool for 0 to m tools that require runtime parameters

``num_params_[0..m]`` - The number of runtime parameters for the tool between 0 and m

``param_label_[0..m]_[0..x]`` - The parameter label for the tool between 0 and m and the parameter for that tool between 0 and x

``param_[0..m]_[0..x]`` - The parameter value for the tool between 0 and m and the parameter for that tool between 0 and x

Usage
-----

**Environment variables GALAXY_URL and GALAXY_KEY must be set before this application can be used.**

Then, execute the ``gflow`` command as so:

    $ gflow config/config.ini

Or, if running from the source directory without having installed the application:

    $ ./gflow-runner.py config/config.ini
    
Tests
-----

After setting the envionment variables mentioned above, execute the tests with:

    $ nosetests
    
A small number of data files and workflow files have been included in ``data/`` and ``workflow/`` for testing purposes.
