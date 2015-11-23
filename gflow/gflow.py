import sys
import json
import logging
from input import Input
from bioblend.galaxy.objects import *


class GFlow(object):
    """
    Interact with a Galaxy instance.

    Args:
        config: An object that holds the parameters pulled from a config file.
    Attributes:
        options (dict): A dictionary to hold all the parameters provided by the config argument.
    """

    def __init__(self, config):
        self.logger = logging.getLogger('gflow.GFlow')
        self.options = config
        self.__datasets = []
        for i in range(0, self.options.num_datasets):
            self.__datasets.append(Input(self.options.dataset_src, self.options.datasets[i], self.options.labels[i]))

    def import_workflow(self, gi):
        """
        Import a workflow into an instance of Galaxy.

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the workflow to.
        Returns:
            The workflow object created.
        """
        if self.options.workflow_src == 'local':
            workflow_json = json.load(open(self.options.workflow))
            wf = gi.workflows.import_new(workflow_json)
        elif self.options.workflow_src == 'id':
            wf = gi.workflows.get(self.options.workflow)
        else:
            wf = gi.workflows.import_shared(self.options.workflow)          # No shared URL to test yet
        return wf

    def import_data(self, library):
        """
        Import a dataset into a library of an instance of Galaxy.

        Args:
            library (Library): The library to upload the dataset to
        Returns:
            results (LibraryDataset): Dataset object that represents the uploaded content if successful,
                                      None if not successful
        """
        results = None
        for i in range(0, len(self.__datasets)):
            self.logger.debug("Dataset source: '%s'" % self.__datasets[i].input_type)
            if self.__datasets[i].input_type == 'local':
                results = library.upload_from_local(self.__datasets[i].name)
            elif self.__datasets[i].input_type == 'url':
                results = library.upload_from_url(self.__datasets[i].name)      # Need a URL to test
            else:
                try:
                    results = library.upload_from_galaxy_fs(self.__datasets[i].name)        # Still doesn't work
                except:
                    self.logger.error("File upload unsuccessful, only admins can "
                                      "upload files from the Galaxy filesystem")
                    e = sys.exc_info()[0]
                    self.logger.error(e)
        return results

    def set_tool_params(self):
        """
        Map the parameters of tools to the ID of each tool.

        Returns:
            params (dict): The dictionary containing the tool IDs and parameters.
        """
        params = {}
        for i in range(0, self.options.num_tools):
            params[self.options.step_ids[i]] = self.options.tool_params[i]
        return params

    def run_workflow(self):
        """
        Make connection, import workflow, create data library, import data, create output history,
        and run the workflow in Galaxy.

        Returns:
             results (tuple): List of output datasets and output history if successful, None if not successful.
        """
        self.logger.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.options.galaxy_url, self.options.galaxy_key)

        self.logger.info("Importing workflow")
        workflow = self.import_workflow(gi)
        if not workflow.is_runnable:
            self.logger.error("Workflow not runnable, missing required tools")
            return

        self.logger.info("Creating data library '%s'" % self.options.library)
        library = gi.libraries.create(self.options.library)

        self.logger.info("Importing data")
        self.import_data(library)

        self.logger.info("Creating output history '%s'" % self.options.outputhist)
        outputhist = gi.histories.create(self.options.outputhist)

        self.logger.info("Creating input map")
        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        results = None

        if self.options.num_tools:
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

        return results
