import sys
import json
import logging
import yaml
import os
from bioblend.galaxy.objects import *


class GFlow(object):

    def __init__(self, configfile):
        """
        Interact with a Galaxy instance.

        Args:
            configfile (str): The location of a config file.
        Attributes:
            self.logger: For logging.
            self.cfg (dict): A dictionary to hold all the parameters provided by the config argument.
            self.galaxy_url (str): The URL of an instance of Galaxy
            self.galaxy_key (str): The API key of an instance of Galaxy
        """
        self.logger = logging.getLogger('gflow.GFlow')
        self.logger.info("Reading config file")
        with open(configfile, "r") as ymlfile:
            self.cfg = yaml.load(ymlfile)
        self.logger.info("Reading Galaxy credentials")
        self.galaxy_url = os.environ.get("GALAXY_URL", None)
        self.galaxy_key = os.environ.get("GALAXY_KEY", None)
        if not self.galaxy_key or not self.galaxy_url:
            self.logger.error("GALAXY_URL and/or GALAXY_KEY environment variable(s) not set")
            raise IOError  # TO BE CHANGED

    def import_workflow(self, gi):
        """
        Import a workflow into an instance of Galaxy.

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the workflow to.
        Returns:
            The workflow object created.
        """
        if self.cfg['workflow']['workflow_src'] == 'local':
            workflow_json = json.load(self.cfg['workflow']['workflow'])
            wf = gi.workflows.import_new(workflow_json)
        elif self.cfg['workflow']['workflow_src'] == 'id':
            wf = gi.workflows.get(self.cfg['workflow']['workflow'])
        else:
            wf = gi.workflows.import_shared(self.cfg['workflow']['workflow'])          # No shared URL to test yet
        return wf

    def import_data(self, library):
        """
        Import a dataset into a library of an instance of Galaxy.

        Args:
            library (Library): The library to upload the dataset(s) to
        Returns:
            results (LibraryDataset): Dataset object that represents the uploaded content if successful,
                                      None if not successful
        """
        results = None
        for i in range(0, len(self.cfg['input']['datasets'])):
            self.logger.debug("Dataset source: '%s'" % self.cfg['input']['dataset_src'])
            if self.cfg['input']['dataset_src'] == 'local':
                results = library.upload_from_local(self.cfg['input']['datasets']['dataset_' + str(i)]['data'])
            elif self.cfg['input']['dataset_src'] == 'url':
                results = library.upload_from_url(self.cfg['input']['datasets'][str(i)]['data'])   # Need a URL to test
            else:
                try:
                    results = library.upload_from_galaxy_fs(self.cfg['input']['datasets'][str(i)]['data'])
                except:
                    self.logger.error("File upload unsuccessful, only admins can "
                                      "upload files from the Galaxy filesystem")
                    e = sys.exc_info()[0]
                    self.logger.error(e)
        return results

    def set_tool_params(self):
        """
        Map the parameters of tools requiring runtime parameters to the step ID of each tool.

        Returns:
            params (dict): The dictionary containing the step IDs and parameters.
        """
        params = {}
        for i in range(0, len(self.cfg['tool_runtime_params'])):
            param_dict = {}
            for j in range(0, len(self.cfg['tool_runtime_params']['tool_' + str(i)]['params'])):
                param_dict[self.cfg['tool_runtime_params']['tool_' + str(i)]['params']['param_' + str(j)]
                    ['param_name']] = self.cfg['tool_runtime_params']['tool_0']['params']['param_0']['param_value']
            params[self.cfg['tool_runtime_params']['tool_' + str(i)]['step_id']] = param_dict
        return params

    def run_workflow(self):
        """
        Make connection, import workflow, create data library, import data, create output history,
        and run the workflow in Galaxy.

        Returns:
             results (tuple): List of output datasets and output history if successful, None if not successful.
        """
        self.logger.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.galaxy_url, self.galaxy_key)

        self.logger.info("Importing workflow")
        workflow = self.import_workflow(gi)
        if not workflow.is_runnable:
            self.logger.error("Workflow not runnable, missing required tools")
            return

        self.logger.info("Creating data library '%s'" % self.cfg['library'])
        library = gi.libraries.create(self.cfg['library'])

        self.logger.info("Importing data")
        self.import_data(library)

        self.logger.info("Creating output history '%s'" % self.cfg['output'])
        outputhist = gi.histories.create(self.cfg['output'])

        self.logger.info("Creating input map")
        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        results = None

        if self.cfg['tool_runtime_params']:
            self.logger.info("Setting runtime tool parameters")
            params = self.set_tool_params()
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist, params)
        else:
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist)

        if results:
            self.logger.info("Workflow finished successfully")
        else:
            self.logger.error("Workflow did not finish")

        print results
        return results
