import unittest
from gflow.config import *
from nose.tools import raises

class TestConfig(unittest.TestCase):

    def test_proper_number_of_datasets(self):
        options = Config("tests/config/config0.ini")
        self.assertEqual(options.num_datasets, len(options.datasets))

    def test_proper_number_of_labels(self):
        options = Config("tests/config/config0.ini")
        self.assertEqual(options.num_datasets, len(options.labels))

    @raises(SystemExit)
    def test_more_datasets_declared_than_given(self):
        Config("tests/config/config1.ini")

    @raises(SystemExit)
    def test_improper_dataset_src(self):
        Config("tests/config/config2.ini")

    @raises(SystemExit)
    def test_improper_workflow_src(self):
        Config("tests/config/config3.ini")

    @raises(SystemExit)
    def test_more_tools_declared_than_given(self):
        Config("tests/config/config4.ini")

    @raises(SystemExit)
    def test_missing_value(self):
       Config("tests/config/config5.ini")

    @raises(SystemExit)
    def test_missing_or_misspelled_option(self):
        Config("tests/config/config6.ini")

    @raises(SystemExit)
    def test_more_datasets_given_than_required(self):
        Config("tests/config/config7.ini")