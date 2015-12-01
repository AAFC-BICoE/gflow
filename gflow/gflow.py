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
        self.check_for_empty_values(self.cfg)
        self.logger.info("Reading Galaxy credentials")
        self.galaxy_url = os.environ.get("GALAXY_URL", None)
        self.galaxy_key = os.environ.get("GALAXY_KEY", None)
        if not self.galaxy_key or not self.galaxy_url:
            self.logger.error("GALAXY_URL and/or GALAXY_KEY environment variable(s) not set")
            raise ValueError

    def check_for_empty_values(self, d):
        if isinstance(d, dict):
            for k in d:
                self.check_for_empty_values(d[k])
        else:
            if d is None:
                self.logger.error("Missing required value in config file")
                raise RuntimeError()

    def import_workflow(self, gi):
        """
        Import a workflow into an instance of Galaxy.

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the workflow to.
        Returns:
            wf (Workflow): The workflow object created.
        """
        if self.cfg['workflow']['workflow_src'] == 'local':
            try:
                with open(self.cfg['workflow']['workflow']) as json_file:
                    workflow = json.load(json_file)
                wf = gi.workflows.import_new(workflow)
            except IOError as e:
                self.logger.error(e)
                raise IOError
        elif self.cfg['workflow']['workflow_src'] == 'id':
            wf = gi.workflows.get(self.cfg['workflow']['workflow'])
        elif self.cfg['workflow']['workflow_src'] == 'shared':
            wf = gi.workflows.import_shared(self.cfg['workflow']['workflow'])  # No shared URL to test yet
        else:
            self.logger.error("Workflow source must be local, workflow, or shared")
            raise ValueError
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
            self.logger.debug("Dataset source is '%s'" % self.cfg['input']['dataset_src'])
            if self.cfg['input']['dataset_src'] == 'local':
                try:
                    results = library.upload_from_local(self.cfg['input']['datasets']['dataset_' + str(i)]['data'])
                except IOError as e:
                    self.logger.error(e)
                    raise IOError
            elif self.cfg['input']['dataset_src'] == 'url':
                results = library.upload_from_url(self.cfg['input']['datasets'][str(i)]['data'])  # Need a URL to test
            elif self.cfg['input']['dataset_src'] == "galaxyfs":
                try:
                    results = library.upload_from_galaxy_fs(self.cfg['input']['datasets'][str(i)]['data'])
                except:
                    self.logger.error("File upload unsuccessful, only admins can "
                                      "upload files from the Galaxy filesystem")
                    e = sys.exc_info()[0]
                    self.logger.error(e)
            else:
                self.logger.error("Dataset source must be local, url, or galaxyfs")
                raise ValueError
        return results

    def set_tool_params(self, wf):
        """
        Map the parameters of tools requiring runtime parameters to the step ID of each tool.

        Args:
            wf (Workflow): The workflow object containing the tools
        Returns:
            params (dict): The dictionary containing the step IDs and parameters.
        """
        params = {}
        for i in range(0, len(self.cfg['tool_runtime_params'])):
            param_dict = {}
            for j in range(0, len(self.cfg['tool_runtime_params']['tool_' + str(i)])):
                param_dict[self.cfg['tool_runtime_params']['tool_' + str(i)]['param_' + str(j)]['param_name']] \
                    = self.cfg['tool_runtime_params']['tool_' + str(i)]['param_' + str(j)]['param_value']
                for s in wf.sorted_step_ids():
                    try:
                        if wf.steps[s].tool_inputs[self.cfg['tool_runtime_params']['tool_' + str(i)]
                                                   ['param_' + str(j)]['param_name']]:
                            params[s] = param_dict
                    except KeyError:
                        pass
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
            params = self.set_tool_params(workflow)
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist, params)
        else:
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist)

        if results:
            self.logger.info("Workflow finished successfully")
        else:
            self.logger.error("Workflow did not finish")

        return results
