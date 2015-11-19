import unittest
from gflow.gflow import *
from nose.tools import raises


class TestGFlow(unittest.TestCase):

    def setUp(self):
        self.options = Config("tests/config/config0.ini")
        self.gflow = GFlow(self.options)

    def test_good_workflow(self):
        assert self.gflow.run_workflow() == 0

    def test_good_galaxy_connection(self):
        gi = GalaxyInstance(self.options.galaxy_url, self.options.galaxy_key)
        assert gi

    def test_import_workflow_from_loca_file(self):
        self.options.workflow_src = "local"
        self.options.workflow = "workflows/galaxy101.ga"
        self.gflow = GFlow(self.options)
        assert self.gflow.run_workflow() == 0

    @raises(SystemExit)
    def test_fail_import_dataset_from_galaxfs(self):
        self.options.workflow_src = "local"
        self.options.workflow = "workflows/select_sort.ga"
        self.options.dataset_src = "galaxyfs"
        self.options.dataset = "/mnt/galaxy/files/000/dataset_100.dat"
        self.gflow = GFlow(self.options)
        self.gflow.run_workflow()

    def test_run_workflow_with_no_runtime_tool_params(self):
        self.options = Config("tests/config/config8.ini")
        gflow = GFlow(self.options)
        assert gflow.run_workflow() == 0