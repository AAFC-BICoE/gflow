import unittest
from gflow.GFlow import *
from nose.tools import raises


class TestConfig(unittest.TestCase):

    def test_proper_number_of_datasets(self):
        configfile = "tests/configs/config0.txt"
        options = read_config(configfile)
        self.assertEqual(int(options['num_datasets']), len(options['datasets']))

    def test_proper_number_of_labels(self):
        configfile = "tests/configs/config0.txt"
        options = read_config(configfile)
        self.assertEqual(int(options['num_datasets']), len(options['labels']))

    @raises(SystemExit)
    def test_improper_number_of_datasets_or_labels(self):
        configfile = "tests/configs/config1.txt"
        read_config(configfile)

    def test_proper_workflow_src(self):
        configfile = "tests/configs/config0.txt"
        options = read_config(configfile)
        assert options['workflow_src'] in ['local', 'shared']

    @raises(SystemExit)
    def test_improper_workflow_src(self):
        configfile = "tests/configs/config3.txt"
        read_config(configfile)

    def test_proper_dataset_src(self):
        configfile = "tests/configs/config0.txt"
        options = read_config(configfile)
        assert options['dataset_src'] in ['local', 'url', 'galaxyfs']

    @raises(SystemExit)
    def test_improper_dataset_src(self):
        configfile = "tests/configs/config2.txt"
        read_config(configfile)


class TestGFlow:

    def setup(self):
        configfile = "config.txt"
        options = read_config(configfile)
        self.gflow = GFlow(options)

    def test_good_workflow(self):
        assert self.gflow.run_workflow() == 0

    def test_good_galaxy_connection(self):
        gi = GalaxyInstance(self.gflow.galaxy_url, self.gflow.galaxy_key)
        assert gi
