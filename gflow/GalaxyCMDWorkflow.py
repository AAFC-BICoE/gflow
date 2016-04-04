import json
import logging
import yaml

from bioblend.galaxy.objects import GalaxyInstance
from bioblend.galaxy import dataset_collections as collections


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
            self.history_name (str): The name of the history to be created
            self.workflow_source (str): Whether the workflow's being imported from a file or with an id
            self.workflow (str): Either a filename or id for the workflow
            self.dataset_collection (dict): A list of datasets to make a dataset collection with
            self.datasets (dict): A collection of filenames or URLs for the datasets
            self.runtime_params (dict): A collection of required runtime parameters
            self.library_name (str): The name of the library to be created
        """
        self.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        self.galaxy_url = datadict['galaxy_url']
        self.galaxy_key = datadict['galaxy_key']
        self.history_name = datadict['history_name']
        self.workflow_source = datadict['workflow_source']
        self.workflow = datadict['workflow']
        # Optional parameters follow
        self.dataset_collection = None
        self.datasets = None
        self.runtime_params = None
        self.library_name = None
        unset_params = []
        try:
            self.dataset_collection = datadict['dataset_collection']
        except KeyError as e:
            unset_params.append('dataset_collection')
        try:
            self.datasets = datadict['datasets']
        except KeyError as e:
            unset_params.append('datasets')
        try:
            self.runtime_params = datadict['runtime_params']
        except KeyError as e:
            unset_params.append('runtime_params')
        try:
            self.library_name = datadict['library_name']
        except KeyError as e:
            unset_params.append('library_name')
        self.logger.warning("Parameter(s) not set: %s" % str(unset_params))


    @classmethod
    def init_from_config_file(cls, configfile):
        """
        Makes a GFlow object from a config file

        Args:
            configfile (str): The name of the config file to be read
        """
        cls.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        cls.logger.info("Reading configuration file")
        with open(configfile, "r") as ymlfile:
            config = yaml.load(ymlfile)
        try:
            missing_var = GalaxyCMDWorkflow.verify_config_file(config)
            if missing_var:
                cls.logger.error("Missing value for required parameter '%s'" % missing_var)
                raise ValueError("Missing value for required parameter '%s'" % missing_var)
        except KeyError as e:
            cls.logger.error("Missing required parameter %s" % str(e))
            raise KeyError("Missing required parameter %s" % str(e))
        return cls(config)

    @classmethod
    def init_from_params(cls, galaxy_url, galaxy_key, history_name, workflow_source, workflow,
                         dataset_collection=None, datasets=None, runtime_params=None, library_name=None):
        """
        Makes GFlow object from provided parameters

        Args:
            galaxy_url (str): The URL of an instance of Galaxy
            galaxy_key (str): The API key of an instance of Galaxy
            history_name (str): The name of the history to be created
            workflow_source (str): Whether the workflow's being imported from a file or with an id
            workflow (str): Either a filename or id for the workflow
            dataset_collection (dict): A list of datasets to make a dataset collection with
            datasets (dict): A collection of filenames or URLs for the datasets
            runtime_params (dict): A collection of required runtime parameters
            library_name (str): The name of the library to be created
        """
        cls.logger = logging.getLogger('gflow.GalaxyCMDWorkflow')
        cls.logger.info("Reading from parameters")
        config = {'galaxy_url': galaxy_url, 'galaxy_key': galaxy_key,
                  'history_name': history_name, 'workflow_source': workflow_source, 'workflow': workflow,
                  'dataset_collection': dataset_collection, 'datasets': datasets, 'runtime_params': runtime_params,
                  'library_name': library_name}
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
        for key in ['galaxy_url', 'galaxy_key', 'history_name', 'workflow_source', 'workflow']:
            if config[key] is None:
                return key
        return None

    @staticmethod
    def verify_runtime_params(workflow):
        """
        Check if any runtime parameters are required for the workflow

        Args:
            workflow (Workflow): The Workflow object containing the tool information
        Returns:
            Name of parameter if runtime parameter is required, None otherwise
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
                raise IOError(e)
        elif self.workflow_source == 'id':
            wf = gi.workflows.get(self.workflow)
        else:
            self.logger.error("Workflow source must be either 'local' or 'id'")
            raise ValueError("Workflow source must be either 'local' or 'id'")
        return wf

    def import_datasets(self, data_group_type, gi, history):
        """
        Import the datasets into a history of an instance of Galaxy

        Args:
            data_group_type (str): Either 'datasets' or 'dataset_collection'
            gi (GalaxyInstance): The instance of Galaxy to import the data to
            history (History): The history that the data will be imported to
        Returns:
            results (List): List of datasets imported into the history
        """
        if data_group_type == 'datasets':
            datasets = self.datasets
        elif data_group_type == 'dataset_collection':
            datasets = self.dataset_collection['datasets']
        else:
            self.logger.error("Data group type must be 'datasets' or 'dataset_collection'")
            raise ValueError("Data group type must be 'datasets' or 'dataset_collection'")
        results = []
        for i in range(0, len(datasets)):
            if datasets[i]['source'] == 'local':
                self.logger.info("Importing dataset from file: '%s'" % datasets[i]['dataset_file'])
                try:
                    results.append(history.upload_dataset(datasets[i]['dataset_file']))
                except IOError as e:
                    self.logger.error("Dataset file '%s' does not exist" % datasets[i]['dataset_file'])
                    raise IOError("Dataset file '%s' does not exist" % datasets[i]['dataset_file'])
            elif datasets[i]['source'] == 'library':
                self.logger.info("Importing dataset: '%s' from library: '%s'" % (datasets[i]['dataset_id'],
                                  datasets[i]['library_id']))
                lib = gi.libraries.get(datasets[i]['library_id'])
                dataset = lib.get_dataset(datasets[i]['dataset_id'])
                results.append(history.import_dataset(dataset))
            else:
                self.logger.error("Dataset source must be either 'local' or 'library'")
                raise ValueError("Dataset source must be either 'local' or 'library'")
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
                try:
                    param_dict[self.runtime_params['tool_' + str(i)]['param_' + str(j)]['name']] \
                        = self.runtime_params['tool_' + str(i)]['param_' + str(j)]['value']
                except KeyError as e:
                    self.logger.error("Missing value for %s key in runtime parameters" % e)
                    raise KeyError("Missing value for %s key in runtime parameters" % e)
                for s in wf.sorted_step_ids():
                    try:
                        if wf.steps[s].tool_inputs[self.runtime_params['tool_' + str(i)]['param_' + str(j)]['name']]:
                            params[s] = param_dict
                    except KeyError:
                        pass
        return params

    def create_dataset_collection(self, gi, outputhist, name="DatasetList"):
        """
        Make a dataset collection with the datasets listed in self.dataset_collection

        Args:
            gi (GalaxyInstance): The current instance of Galaxy being used
            outputhist (History): The history in which to create the dataset collection
            name (str): The name of the new dataset collection
        Returns:
            dataset_collection (HistoryDatasetCollectionAssociation): The new dataset collection object
        """
        self.logger.info("Dataset collection name: '%s'" % name)
        collection_elements = []
        datasets = self.import_datasets('dataset_collection', gi, outputhist)
        if self.dataset_collection['type'] == 'list':
            for i in range(0, len(datasets)):
                collection_elements.append(collections.HistoryDatasetElement(name=datasets[i].name, id=datasets[i].id))
        elif self.dataset_collection['type'] == 'list:paired':
            pair_num = 1
            for i in range(0, len(datasets), 2):
                collection_elements.append(
                    collections.CollectionElement(
                        name=datasets[i].name,
                        type='paired',
                        elements=[
                            collections.HistoryDatasetElement(name='forward', id=datasets[i].id),
                            collections.HistoryDatasetElement(name='reverse', id=datasets[i+1].id),
                        ]
                    )
                )
                pair_num += 1
        else:
            self.logger.error("Dataset collection type must be 'list' or 'list:paired'")
            raise ValueError("Dataset collection type must be 'list' or 'list:paired'")
        collection_description = collections.CollectionDescription(
                name=name,
                type=self.dataset_collection['type'],
                elements=collection_elements
            )
        dataset_collection = outputhist.create_dataset_collection(collection_description)
        return dataset_collection

    def run(self, temp_wf=False, output_file=None):
        """
        Make the connection, set up for the workflow, then run it

        Args:
            temp_wf (bool): Flag to determine whether the workflow should be deleted after use
        Returns:
            results (tuple): List of output datasets and output history if successful, None if not successful
        """
        self.logger.info("Initiating Galaxy connection")
        gi = GalaxyInstance(self.galaxy_url, self.galaxy_key)

        self.logger.info("Importing workflow '%s' from '%s' source" % (self.workflow,  self.workflow_source))
        workflow = self.import_workflow(gi)
        if not workflow.is_runnable:
            self.logger.error("Workflow not runnable, missing required tools")
            raise RuntimeError("Workflow not runnable, missing required tools")

        self.logger.info("Creating output history '%s'" % self.history_name)
        outputhist = gi.histories.create(self.history_name)

        input_map = dict()
        if self.dataset_collection:
            self.logger.info("Creating dataset collection")
            dataset_collection = self.create_dataset_collection(gi, outputhist)
            input_map[self.dataset_collection['input_label']] = dataset_collection

        datasets = []
        if self.datasets:
            self.logger.info("Importing datasets to history")
            imported_datasets = self.import_datasets('datasets', gi, outputhist)
            for i in range(0, len(imported_datasets)):
                input_map[self.datasets[i]['input_label']] = imported_datasets[i]

        if self.library_name:
            self.logger.info("Creating library '%s'" % self.library_name)
            lib = gi.libraries.create(self.library_name)
            self.logger.info("Copying datasets to library '%s'" % self.library_name)
            for data in outputhist.get_datasets():
                lib.copy_from_dataset(data)

        if self.runtime_params:
            self.logger.info("Setting runtime tool parameters")
            params = self.set_runtime_params(workflow)
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist, params)
        else:
            self.logger.info("Checking for missing tool parameters")
            missing_param = self.verify_runtime_params(workflow)
            if missing_param:
                self.logger.error("Missing runtime parameter for '%s'" % str(missing_param))
                raise RuntimeError("Missing runtime parameter for '%s'" % str(missing_param))
            self.logger.info("Initiating workflow")
            results = workflow.run(input_map, outputhist)
            if output_file:
                f = open(output_file, 'w')
                f.write(str(results))
                f.close()

        if temp_wf and self.workflow_source != 'id':
            self.logger.info("Deleting workflow: '%s'" % self.workflow)
            workflow.delete()

        return results
