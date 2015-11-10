# -*- coding: utf-8 -*-


"""gflow.gflow: provides entry point main()."""


__version__ = "0.2.0"


import getopt
import sys
import ConfigParser
from bioblend import galaxy

class gflow():
	"""Object that interacts with Galaxy"""
	def __init__(self,galaxy_url,galaxy_key,library_name,dataset_src,
				 num_datasets,datasets,output_history_name,workflow_src,
				 input_label,workflow):
		self.galaxy_url = galaxy_url
		self.galaxy_key = galaxy_key
		self.library_name = library_name
		self.dataset_src = 
		
	def run_workflow():
		pass

