# -*- coding: utf-8 -*-


"""gflow.gflow: provides entry point main()."""


__version__ = "0.2.0"


import getopt
import sys
import ConfigParser
import json
import logging
from Input import Input
from bioblend.galaxy.objects import *


def print_usage(outstream):
    usage = ("Usage: gflow.py [options] config.txt\n"
             "  Options:\n"
             "    -h|--help           print this help message and exit")
    print >> outstream, usage


def read_config(configfile):
    config = ConfigParser.RawConfigParser()
    config.read(configfile)
    options = dict()
    options['galaxy_url'] = config.get('galaxy', 'galaxy_url')
    options['galaxy_key'] = config.get('galaxy', 'galaxy_key')
    options['library_name'] = config.get('library', 'library_name')
    options['dataset_src'] = config.get('input', 'dataset_src')
    options['num_datasets'] = config.get('input', 'num_datasets')
    options['datasets'] = []
    options['labels'] = []
    for i in range(0, int(options['num_datasets'])):
        options['datasets'].append(config.get('input', "data" + str(i)))
        options['labels'].append(config.get('input', "label" + str(i)))
    options['output_history_name'] = config.get('output', 'output_history_name')
    options['workflow_src'] = config.get('workflow', 'source')
    options['workflow'] = config.get('workflow', 'workflow')
    return options


def parse_options():
    outstream = sys.stdout
    optstr = "h:"
    longopts = ["help"]
    try:
        (options, args) = getopt.getopt(sys.argv[1:], optstr, longopts)
    except getopt.GetoptError as e:
        print >> sys.stderr, e
        sys.exit(1)
    for key, value in options:
        if key in ("-h", "--help"):
            print_usage(outstream)
            sys.exit(0)
        else:
            pass
    configfile = None
    if len(args) > 0:
        configfile = args[0]
        try:
            instream = open(configfile, "r")
        except IOError as e:
            print >> sys.stderr, "ERROR: Opening config file %s" % configfile
            print >> sys.stderr, e
            sys.exit(1)
    elif not sys.stdin.isatty():
        instream = sys.stdin
    else:
        print >> sys.stderr, "ERROR: Please provide a config file"
        print_usage(sys.stderr)
        sys.exit(1)
    instream.close()
    return configfile


class GFlow(object):

    """Object that interacts with Galaxy"""
    def __init__(self, options):
        self.galaxy_url = options['galaxy_url']
        self.galaxy_key = options['galaxy_key']
        self.library_name = options['library_name']
        self.output_history_name = options['output_history_name']
        self.workflow_src = options['workflow_src']
        self.workflow = options['workflow']
        self.datasets = self.collect_datasets(options['dataset_src'], options['datasets'], options['labels'])

    def import_workflow(self, gi):
        if self.workflow_src == 'local':
            workflow_json = json.load(open(self.workflow))
            wf = gi.workflows.import_new(workflow_json)
        elif self.workflow_src == 'shared':
            wf = gi.workflows.import_shared(self.workflow)
        else:
            print >> sys.stderr, "ERROR: Accepted workflow sources are: local or shared"
            sys.exit(1)
        return wf

    def collect_datasets(self, src, datasets, labels):
        sets = []
        for i in range(0, len(datasets)):
            sets.append(Input(src, datasets[i], labels[i]))
        return sets

    def import_data(self, library):
        for i in range(0, len(self.datasets)):
            if self.datasets[i].input_type == 'local':
                library.upload_from_local(self.datasets[i].name)
            elif self.datasets[i].input_type == 'url':
                library.upload_from_url(self.datasets[i].name)
            elif self.datasets[i].input_type == 'galaxyfs':
                library.upload_from_galaxy_filesystem(self.datasets[i].name)
            else:
                print >> sys.stderr, "ERROR: Accepted dataset sources are: local, url, or galaxyfs"
            return True

    def run_workflow(self):
        logging.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.galaxy_url, self.galaxy_key)

        logging.info("Importing workflow")
        workflow = self.import_workflow(gi)

        logging.info("Creating data library '%s'" % self.library_name)
        library = gi.libraries.create(self.library_name)

        logging.info("Importing data")
        self.import_data(library)

        logging.info("Creating output history '%s'" % self.output_history_name)
        outputhist = gi.histories.create(self.output_history_name)

        input_map = dict(zip(workflow.input_labels, library.get_datasets()))

        if workflow.is_runnable:
            logging.info("Initiating workflow")
            workflow.run(input_map, outputhist)
            logging.info("Workflow finished successfully")
        else:
            print >> sys.stderr, "ERROR: Workflow not runnable"
            sys.exit(1)

def main():
    logging.basicConfig(filename='gflow.log', level=logging.INFO)
    configfile = parse_options()
    options = read_config(configfile)
    gflow = GFlow(options)
    gflow.run_workflow()