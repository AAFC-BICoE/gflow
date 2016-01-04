import json
import logging
import yaml
from yaml import parser
from bioblend.galaxy.objects import GalaxyInstance


class GalaxyCMDWorkflow(object):
    def __init__(self, datadict):
        """
        Interact with a Galaxy instance

        Args:
            datadict (dict): The dictionary containing configuration parameters.
        Attributes:
            self.logger: For logging.
            self.galaxy_url (str): The URL of an instance of Galaxy
            self.galaxy_key (str): The API key of an instance of Galaxy
            self.library_name (str): The name of the library to be created
            self.history_name (str): The name of the history to be created
            self.workflow_source (str): Whether the workflow's being imported from a file or with an id
            self.workflow (str): Either a filename or id for the workflow
            self.datasets (dict): A collection of filenames or URLs for the datasets
            self.runtime_params (dict): A collection of required runtime parameters
        """
        self.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        self.galaxy_url = datadict['galaxy_url']
        self.galaxy_key = datadict['galaxy_key']
        self.library_name = datadict['library_name']
        self.history_name = datadict['history_name']
        self.workflow_source = datadict['workflow_source']
        self.workflow = datadict['workflow']
        # Optional parameters follow
        self.datasets = None
        self.runtime_params = None
        try:
            self.datasets = datadict['datasets']
            self.runtime_params = datadict['runtime_params']
        except KeyError as e:
            self.logger.warning("%s parameter(s) not set", e)

    @classmethod
    def init_from_config_file(cls, configfile):
        """
        Makes a GFlow object from a config file

        Args:
            configfile (str): The name of the config file to be read
        """
        cls.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        cls.logger.info("Reading configuration file")
        try:
            with open(configfile, "r") as ymlfile:
                config = yaml.load(ymlfile)
        except parser.ParserError:
            cls.logger.error("Incorrect yaml syntax in config file")
            raise parser.ParserError
        try:
            missing_var = GalaxyCMDWorkflow.verify_config_file(config)
            if missing_var:
                cls.logger.error("Missing value for required parameter: " + missing_var)
                raise ValueError("Missing value for required parameter: " + missing_var)
        except KeyError as e:
            cls.logger.error("Missing required parameter: " + str(e))
            raise KeyError("Missing required parameter: " + str(e))
        return cls(config)

    @classmethod
    def init_from_params(cls, galaxy_url=None, galaxy_key=None, library_name=None, history_name=None,
                         workflow_source=None, workflow=None, datasets_source=None, datasets=None, runtime_params=None):
        """
        Makes GFlow object from provided parameters

        Args:
            galaxy_url (str): The URL of an instance of Galaxy
            galaxy_key (str): The API key of an instance of Galaxy
            library_name (str): The name of the library to be created
            history_name (str): The name of the history to be created
            workflow_source (str): Whether the workflow's being imported from a file or with an id
            workflow (str): Either a filename or id for the workflow
            datasets (List): A collection of filenames or URLs for the datasets
            runtime_params (dict): A collection of required runtime parameters
        """
        cls.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        cls.logger.info("Reading from parameters")
        config = {'galaxy_url': galaxy_url, 'galaxy_key': galaxy_key, 'library_name': library_name,
                  'history_name': history_name, 'workflow_source': workflow_source, 'workflow': workflow,
                  'datasets_source': datasets_source, 'datasets': datasets, 'runtime_params': runtime_params}
        return cls(config)

    @staticmethod
    def verify_config_file(config):
        """
        Make sure no values of required parameters are missing from the config file

        Args:
            config (dict): The config dictionary containing the key value pairs pulled from the config file
        Returns:
            Raises ValueError if an empty value is found, None otherwise
        """
        for key in ['galaxy_url', 'galaxy_key', 'library_name', 'history_name', 'workflow_source', 'workflow']:
            if config[key] is None:
                return key
        return None

    @staticmethod
    def verify_runtime_params(workflow):
        """
        Check for missing runtime parameters required for workflow

        Args:
            workflow (Workflow): The Workflow object containing the tool information
        Returns:
            Name of parameter if runtime parameter is missing, None otherwise
        """
        for step in workflow.sorted_step_ids():
            values = workflow.steps[step].tool_inputs.viewvalues()
            for i in values:
                if isinstance(i, dict):
                    more_values = i.viewvalues()
                    for j in more_values:
                        if str(j) == "RuntimeValue":
                            return [key for key, value in workflow.steps[step].tool_inputs.iteritems() if value == i]
        return None

    def import_workflow(self, gi):
        """
        Import a workflow into an instance of Galaxy

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the workflow to
        Returns:
            wf (Workflow): The workflow object created
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
            self.logger.error("Workflow source must be either 'local' or 'id'")
            raise ValueError("Workflow source must be either 'local' or 'id'")
        return wf

    def import_data(self, gi, history):
        """
        Upload a dataset into a history of an instance of Galaxy

        Args:
            gi (GalaxyInstance): The instance of Galaxy to import the data to
            history (History): The history that the data will be imported to
        Returns:
            results (List): List of datasets imported into the history
        """
        results = []
        for i in range(0, len(self.datasets)):
            self.logger.info("Dataset %d source: '%s'", i, self.datasets[i]['source'])
            if self.datasets[i]['source'] == 'local':
                self.logger.info("Uploading dataset: " + self.datasets[i]['dataset_id'])
                try:
                    results.append(history.upload_dataset(self.datasets[i]['dataset_id']))
                except IOError as e:
                    self.logger.error(e)
                    raise IOError
            elif self.datasets[i]['source'] == 'library':
                self.logger.info("Importing dataset: " + self.datasets[i]['dataset_id'] + " from library: " +
                                  self.datasets[i]['library_id'])
                lib = gi.libraries.get(self.datasets[i]['library_id'])
                dataset = lib.get_dataset(self.datasets[i]['dataset_id'])
                results.append(history.import_dataset(dataset))
            else:
                self.logger.error("Dataset source must be either 'local' or 'library'")
                raise ValueError
        return results

    def set_runtime_params(self, wf):
        """
        Map the parameters of tools requiring runtime parameters to the step ID of each tool

        Args:
            wf (Workflow): The workflow object containing the tools
        Returns:
            params (dict): The dictionary containing the step IDs and parameters
        """
        params = {}
        for i in range(0, len(self.runtime_params)):
            param_dict = {}
            for j in range(0, len(self.runtime_params['tool_' + str(i)])):
                param_dict[self.runtime_params['tool_' + str(i)]['param_' + str(j)]['name']] \
                    = self.runtime_params['tool_' + str(i)]['param_' + str(j)]['value']
                for s in wf.sorted_step_ids():
                    try:
                        if wf.steps[s].tool_inputs[self.runtime_params['tool_' + str(i)]['param_' + str(j)]['name']]:
                            params[s] = param_dict
                    except KeyError:
                        pass
        return params

    def run(self, temp_wf):
        """
        Make the connection, set up for the workflow, then run it

        Args:
            temp_wf (bool): Flag to determine whether the workflow should be deleted after use
        Returns:
             results (tuple): List of output datasets and output history if successful, None if not successful
        """
        self.logger.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.galaxy_url, self.galaxy_key)

        self.logger.info("Workflow source: %s" % self.workflow_source)
        self.logger.info("Importing workflow from: %s" % self.workflow)
        workflow = self.import_workflow(gi)
        if not workflow.is_runnable:
            self.logger.error("Workflow not runnable, missing required tools")
            raise RuntimeError("Workflow not runnable, missing required tools")

        self.logger.info("Creating output history: '%s'" % self.history_name)
        outputhist = gi.histories.create(self.history_name)

        input_map = dict()
        if self.datasets:
            self.logger.info("Importing datsets to history")
            self.import_data(gi, outputhist)
            input_map = dict(zip(workflow.input_labels, outputhist.get_datasets()))

        if self.runtime_params:
            self.logger.info("Setting runtime tool parameters")
            try:
                params = self.set_runtime_params(workflow)
            except KeyError as e:
                self.logger.error("Missing value for required parameter: %s", e)
                raise KeyError("Missing required parameter for: %s", e)
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist, params)
        else:
            missing_param = self.verify_runtime_params(workflow)
            if missing_param:
                self.logger.error("Missing runtime parameter for: " + str(missing_param))
                raise RuntimeError("Missing runtime parameter for: " + str(missing_param))
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist)

        if temp_wf and self.workflow_source is not 'id':
            gi.workflows.delete(workflow.id)

        return results

# Test for making GFlow object with params
if __name__ == '__main__':
    datasets = ['data/exons.bed', 'data/SNPs.bed']
    runtime_params = {'tool_0': {'param_0': {'name': 'lineNum', 'value': 10}}}
    gflow = GalaxyCMDWorkflow.init_from_params('http://10.117.231.27', 'd2e3a6e000eddd713a15307e3bedfd61',
                                               'Params Library', 'Params History', 'local', 'workflows/galaxy101.ga',
                                               'local', datasets, runtime_params)
    gflow.run(False)
