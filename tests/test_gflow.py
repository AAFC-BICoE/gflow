import os
import pytest
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance

from gflow.GalaxyCMDWorkflow import GalaxyCMDWorkflow


class TestGFlow:

    def setup_class(self):
        galaxy_key = os.environ['GALAXY_API_KEY']
        galaxy_url = os.environ['GALAXY_URL']
        self.gflow = GalaxyCMDWorkflow.init_from_params(galaxy_url, galaxy_key, "Test History", "local",
                                                   "workflows/galaxy101.ga")
        self.gi = galaxy_instance.GalaxyInstance(self.gflow.galaxy_url, self.gflow.galaxy_key)

    def teardown_class(self):
        self.gflow = None

    def test_config_file_missing_required_parameter_is_rejected(self, tmpdir):
        p = tmpdir.mkdir("sub").join("tmp_config.yml")
        p.write("empty: something")
        tmp_config = str(p.dirpath() + "/tmp_config.yml")
        with pytest.raises(KeyError) as excinfo:
            GalaxyCMDWorkflow.init_from_config_file(tmp_config)
        assert 'Missing required parameter \'galaxy_url\'' in str(excinfo.value)

    def test_config_file_missing_value_for_required_param_is_rejected(self, tmpdir):
        p = tmpdir.mkdir("sub").join("tmp_config.yml")
        p.write("galaxy_url: ")
        tmp_config = str(p.dirpath() + "/tmp_config.yml")
        with pytest.raises(ValueError) as excinfo:
            GalaxyCMDWorkflow.init_from_config_file(tmp_config)
        assert 'Missing value for required parameter \'galaxy_url\'' in str(excinfo.value)

    def test_config_file_with_all_required_values_is_accepted(self, tmpdir):
        p = tmpdir.mkdir("sub").join("tmp_config.yml")
        p.write("galaxy_url: something\n"
                "galaxy_key: something\n"
                "history_name: something\n"
                "workflow_source: something\n"
                "workflow: something\n")
        tmp_config = str(p.dirpath() + "/tmp_config.yml")
        gflow = GalaxyCMDWorkflow.init_from_config_file(tmp_config)
        assert gflow.galaxy_url == "something"
        assert gflow.galaxy_key == "something"
        assert gflow.history_name == "something"
        assert gflow.workflow_source == "something"
        assert gflow.workflow == "something"

    def test_import_workflow_from_file(self):
        print os.environ['GALAXY_URL']
        print os.environ['GALAXY_API_KEY']
        workflow = self.gflow.import_workflow(self.gi)
        assert workflow.name == "galaxy101-2015 (imported from API)"
        workflow.delete()

    def test_import_id_workflow_from_id(self):
        workflow = self.gflow.import_workflow(self.gi)
        self.gflow.workflow_source = 'id'
        self.gflow.workflow = workflow.id
        workflow_copy = self.gflow.import_workflow(self.gi)
        assert workflow_copy.name == "galaxy101-2015 (imported from API)"
        workflow.delete()
        workflow_copy.delete()

    def test_import_workflow_bad_source(self):
        self.gflow.workflow_source = "wrong"
        with pytest.raises(ValueError) as excinfo:
            self.gflow.import_workflow(self.gi)
        assert "Workflow source must be either 'local' or 'id'" in str(excinfo.value)

    def test_import_workflow_from_nonexistant_file(self):
        self.gflow.workflow_source = "local"
        self.gflow.workflow = "workflows/not_here"
        with pytest.raises(IOError) as excinfo:
            self.gflow.import_workflow(self.gi)
        assert "No such file or directory" in str(excinfo.value)

    def test_import_dataset_from_file(self):
        datasets = dict()
        datasets[0] = {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'}
        self.gflow.datasets = datasets
        history = self.gi.histories.create(self.gflow.history_name)
        imported = self.gflow.import_datasets('datasets', self.gi, history)
        assert len(imported) == 1
        assert imported[0].name == 'exons.bed'
        history.delete(purge=True)

    def test_import_dataset_from_library(self):
        library = self.gi.libraries.create('Test Library')
        library.upload_data("Some data")
        id = library.dataset_ids[0]
        self.gflow.datasets[0] = {'source': 'library', 'dataset_id': id, 'library_id': library.id,
                                  'input_label': 'Exons'}
        history = self.gi.histories.create(self.gflow.history_name)
        imported = self.gflow.import_datasets('datasets', self.gi, history)
        assert len(imported) == 1
        assert imported[0].name == 'Pasted Entry'
        history.delete(purge=True)
        library.delete()
