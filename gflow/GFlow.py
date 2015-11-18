# -*- coding: utf-8 -*-


"""gflow.gflow: provides entry point main()."""


__version__ = "0.2.0"


import sys
import json
import logging
from Input import Input
from Config import Config
from bioblend.galaxy.objects import *


class GFlow(object):

    """Object that interacts with Galaxy"""
    def __init__(self, config):
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
            wf = gi.workflows.import_shared(self.options.workflow)
        return wf

    def import_data(self, gi):
        if not self.options.new_library:
            library = gi.libraries.get(self.options.library)
        else:
            logging.info("Creating data library '%s'" % self.options.library)
            library = gi.libraries.create(self.options.library)
            logging.info("Importing data")
            for i in range(0, len(self.datasets)):
                if self.datasets[i].input_type == 'local':
                    library.upload_from_local(self.datasets[i].name)
                elif self.datasets[i].input_type == 'url':
                    library.upload_from_url(self.datasets[i].name)
                else:
                    try:
                        library.upload_from_galaxy_fs(self.datasets[i].name)
                    except:
                        print >> sys.stderr, "ERROR: File upload unsuccessful, only admins can " \
                                             "upload files from the Galaxy filesystem"
                        e = sys.exc_info()[0]
                        print >> sys.stderr, e
                    sys.exit(1)
        return library

    def set_tool_params(self):
        params = {}
        for i in range(0, self.options.num_tools):
            params = {self.options.step_ids[i]: self.options.tool_params[i]}
        return params

    def run_workflow(self):
        logging.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.options.galaxy_url, self.options.galaxy_key)

        logging.info("Importing workflow")
        workflow = self.import_workflow(gi)

        library = self.import_data(gi)

        logging.info("Creating output history '%s'" % self.options.outputhist)
        outputhist = gi.histories.create(self.options.outputhist)

        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        if workflow.is_runnable:
            logging.info("Initiating workflow")
            if self.options.num_tools:
                params = self.set_tool_params()
                workflow.run(input_map, outputhist, params)
            else:
                workflow.run(input_map, outputhist)
            logging.info("Workflow finished successfully")
        else:
            print >> sys.stderr, "ERROR: Workflow not runnable"
            sys.exit(1)
        return 0


def main():
    logging.basicConfig(filename='gflow.log', level=logging.INFO)
    options = Config()
    gflow = GFlow(options)
    gflow.run_workflow()
