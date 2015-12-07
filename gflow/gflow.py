import json
import logging
import yaml
import os
from bioblend.galaxy.objects import *


class GFlow(object):
    def __init__(self, configfile=None, galaxy_url=None, galaxy_key=None, library_name=None, history_name=None,
                 workflow_source=None, workflow=None, datasets_source=None, datasets=None, runtime_params=None):
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
        if configfile:
            self.logger.info("Reading configuration file")
            with open(configfile, "r") as ymlfile:
                config = yaml.load(ymlfile)
            self.logger.info("Checking config file for empty values")
            self.check_for_empty_values(config)
            try:
                self.galaxy_url = config['galaxy_url']
                self.galaxy_key = config['galaxy_key']
                self.library_name = config['library']
                self.history_name = config['history']
                self.workflow_source = config['workflow_source']
                self.workflow = config['workflow']
            except KeyError:
                self.logger.error("Missing required parameter(s)")
                raise KeyError
            # Optional parameters follow
            self.datasets_source = None
            self.datasets = None
            self.runtime_params = None
            try:
                if config['datasets_source']:
                    self.datasets_source = config['datasets_source']
                if config['datasets']:
                    self.datasets = config['datasets']
                if config['runtime_params']:
                    self.runtime_params = config['runtime_params']
            except KeyError:
                pass
        else:
            if not galaxy_url or not galaxy_key or not library_name or not history_name or not workflow_source \
                    or not workflow:
                self.logger.error("Missing required parameter(s)")
                raise RuntimeError()
            self.galaxy_url = galaxy_url
            self.galaxy_key = galaxy_key
            self.library_name = library_name
            self.history_name = history_name
            self.workflow_source = workflow_source
            self.workflow = workflow
            # Optional parameters follow
            self.datasets_source = None
            self.datasets = None
            self.runtime_params = None
            if datasets_source:
                self.datasets_source = datasets_source
            if datasets:
                self.datasets = datasets
            if runtime_params:
                self.runtime_params = runtime_params

    def check_for_empty_values(self, config):
        """
        Make sure no required values are missing in the config file.

        Args:
            config (dict): The config dictionary containing the key value pairs pulled from the config file.
        Returns:
            True is successful, raises RuntimeError if a value is empty.
        """
        if isinstance(config, dict):
            for k in config:
                self.check_for_empty_values(config[k])
        else:
            if config is None:
                self.logger.error("Missing required value in config file")
                raise RuntimeError()
        return True

    def check_for_runtime_params(self, workflow):
        """
        Make sure no required values are missing in the config file.

        Args:
            config (dict): The config dictionary containing the key value pairs pulled from the config file.
        Returns:
            True is successful, raises RuntimeError if a value is empty.
        """
        for s in workflow.sorted_step_ids():
            values = workflow.steps[s].tool_inputs.viewvalues()
            for i in values:
                if isinstance(i, dict):
                    more_values = i.viewvalues()
                    for j in more_values:
                        if str(j) == "RuntimeValue":
                            return True
        return False

    def import_workflow(self, gi):
        """
        Import a workflow into an instance of Galaxy.

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the workflow to.
        Returns:
            wf (Workflow): The workflow object created.
        """
        if self.workflow_source == 'local':
            try:
                with open(self.workflow) as json_file:
                    workflow = json.load(json_file)
                wf = gi.workflows.import_new(workflow)
            except IOError as e:
                self.logger.error(e)
                raise IOError
        elif self.workflow_source == 'id':
            wf = gi.workflows.get(self.workflow)
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
        for i in range(0, len(self.datasets)):
            self.logger.debug("Dataset source is '%s'" % self.datasets_source)
            if self.datasets_source == 'local':
                try:
                    results = library.upload_from_local(self.datasets[i])
                except IOError as e:
                    self.logger.error(e)
                    raise IOError
            elif self.datasets_source == 'url':
                results = library.upload_from_url(self.datasets[i])  # Need a URL to test
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
        for i in range(0, len(self.runtime_params)):
            param_dict = {}
            for j in range(0, len(self.runtime_params['tool_' + str(i)])):
                param_dict[self.runtime_params['tool_' + str(i)]['param_' + str(j)]['name']] \
                    = self.runtime_params['tool_'+str(i)]['param_'+str(j)]['value']
                for s in wf.sorted_step_ids():
                    try:
                        if wf.steps[s].tool_inputs[self.runtime_params['tool_' + str(i)]
                                                   ['param_' + str(j)]['name']]:
                            params[s] = param_dict
                    except KeyError:
                        pass
        return params

    def run_workflow(self):
        """
        Make the connection, set up for the workflow, then run it.

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

        self.logger.info("Creating data library '%s'" % self.library_name)
        library = gi.libraries.create(self.library_name)

        if self.datasets:
            self.logger.info("Importing data")
            self.import_data(library)

        self.logger.info("Creating output history '%s'" % self.history_name)
        outputhist = gi.histories.create(self.history_name)

        self.logger.info("Creating input map")
        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        results = None

        try:
            if self.runtime_params:
                self.logger.info("Setting runtime tool parameters")
                params = self.set_tool_params(workflow)
                self.logger.info("Initiating workflow")
                results = workflow.run(input_map, outputhist, params)
            else:
                if self.check_for_runtime_params(workflow):
                    self.logger.error("Missing runtime paramter(s)")
                    raise ValueError
                self.logger.info("Initiating workflow")
                results = workflow.run(input_map, outputhist)
        except RuntimeError as e:
            self.logger.error(e)
            raise RuntimeError

        if results:
            self.logger.info("Workflow finished successfully")
        else:
            self.logger.error("Workflow did not finish")

        return results
