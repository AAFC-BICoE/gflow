import unittest
from gflow.GFlow import *


class TestGFlow(unittest.TestCase):

    def setUp(self):
        self.options = Config("tests/config/config0.ini")
        self.gflow = GFlow(self.options)

    def test_good_workflow(self):
        assert self.gflow.run_workflow() == 0

    def test_good_galaxy_connection(self):
        gi = GalaxyInstance(self.options.galaxy_url, self.options.galaxy_key)
        assert gi
