import unittest
from gflow.gflow import *


class TestGFlow(unittest.TestCase):

    def setUp(self):
        self.gflow = GFlow("tests/config/config0.yml")