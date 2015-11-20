import sys
import json
import logging
from input import Input
from bioblend.galaxy.objects import *


class GFlow(object):

    def __init__(self, config):

        self.logger = logging.getLogger('gflow.GFlow')

        self.options = config
        self.datasets = []
        for i in range(0, self.options.num_datasets):
            self.datasets.append(Input(self.options.dataset_src, self.options.datasets[i], self.options.labels[i]))

    def import_workflow(self, gi):
        if self.options.workflow_src == 'local':
            workflow_json = json.load(open(self.options.workflow))
            wf = gi.workflows.import_new(workflow_json)
        elif self.options.workflow_src == 'id':
            wf = gi.workflows.get(self.options.workflow)
        else:
            wf = gi.workflows.import_shared(self.options.workflow)          # No shared URL to test yet
        return wf

    def import_data(self, library):
        for i in range(0, len(self.datasets)):
            self.logger.debug("Dataset source: '%s'" % self.datasets[i].input_type)
            if self.datasets[i].input_type == 'local':
                library.upload_from_local(self.datasets[i].name)
            elif self.datasets[i].input_type == 'url':
                library.upload_from_url(self.datasets[i].name)      # Need a URL to test
            else:
                try:
                    library.upload_from_galaxy_fs(self.datasets[i].name)        # Still doesn't work
                except:
                    self.logger.error("File upload unsuccessful, only admins can "
                                      "upload files from the Galaxy filesystem")
                    e = sys.exc_info()[0]
                    self.logger.error(e)
        return 0

    def set_tool_params(self):
        params = {}
        for i in range(0, self.options.num_tools):
            params = {self.options.step_ids[i]: self.options.tool_params[i]}
        return params

    def run_workflow(self):
        self.logger.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.options.galaxy_url, self.options.galaxy_key)

        self.logger.info("Importing workflow")
        workflow = self.import_workflow(gi)

        self.logger.info("Creating data library '%s'" % self.options.library)
        library = gi.libraries.create(self.options.library)

        self.logger.info("Importing data")
        self.import_data(library)

        self.logger.info("Creating output history '%s'" % self.options.outputhist)
        outputhist = gi.histories.create(self.options.outputhist)

        self.logger.info("Creating input map")
        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        results = None
        if workflow.is_runnable:
            if self.options.num_tools:
                self.logger.info("Setting runtime tool parameters")
                params = self.set_tool_params()
                self.logger.info("Initiating workflow")
                results = workflow.run(input_map, outputhist, params)
            else:
                self.logger.info("Initiating workflow")
                results = workflow.run(input_map, outputhist)
        else:
            self.logger.error("Workflow not runnable, missing required tools")

        if results:
            self.logger.info("Workflow finished successfully")
        else:
            self.logger.error("Workflow did not finish")

        return results
