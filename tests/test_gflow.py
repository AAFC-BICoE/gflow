import os
import uuid
import pytest
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance
import bioblend.galaxy.objects.wrappers as wrappers

from gflow.GalaxyCMDWorkflow import GalaxyCMDWorkflow


@pytest.fixture()
def gflow():
    galaxy_key = os.environ['GALAXY_API_KEY']
    galaxy_url = os.environ['GALAXY_URL']
    return GalaxyCMDWorkflow.init_from_params(galaxy_url, galaxy_key, "Test History", "local",
                                              "workflows/galaxy101.ga")

@pytest.fixture()
def gi(gflow):
    return galaxy_instance.GalaxyInstance(gflow.galaxy_url, gflow.galaxy_key)

def test_config_file_missing_required_parameter_is_rejected(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("something: value")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    with pytest.raises(KeyError) as excinfo:
        GalaxyCMDWorkflow.init_from_config_file(tmp_config)
    assert 'Missing required parameter \'galaxy_url\'' in str(excinfo.value)

def test_config_file_missing_value_for_required_param_is_rejected(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("galaxy_url: ")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    with pytest.raises(ValueError) as excinfo:
        GalaxyCMDWorkflow.init_from_config_file(tmp_config)
    assert 'Missing value for required parameter \'galaxy_url\'' in str(excinfo.value)

def test_config_file_with_all_required_values_is_accepted(tmpdir):
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

def test_import_workflow_from_file(gflow, gi):
    workflow = gflow.import_workflow(gi)
    assert workflow.name == "galaxy101-2015_avjasdvuweufwevw9wf (imported from API)"
    workflow.delete()

def test_import_workflow_from_id(gflow, gi):
    workflow = gflow.import_workflow(gi)
    gflow.workflow_source = 'id'
    gflow.workflow = workflow.id
    workflow_copy = gflow.import_workflow(gi)
    assert workflow_copy.name == "galaxy101-2015_avjasdvuweufwevw9wf (imported from API)"
    workflow.delete()
    workflow_copy.delete()

def test_import_workflow_from_bad_source(gflow):
    gflow.workflow_source = "wrong"
    with pytest.raises(ValueError) as excinfo:
        gflow.import_workflow(gi)
    assert "Workflow source must be either 'local' or 'id'" in str(excinfo.value)

def test_import_workflow_from_nonexistant_file(gflow):
    gflow.workflow = "workflows/not_here"
    with pytest.raises(IOError) as excinfo:
        gflow.import_workflow(gi)
    assert "No such file or directory" in str(excinfo.value)

def test_import_dataset_from_file(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'}}
    imported = gflow.import_datasets('datasets', gi, history)
    assert len(imported) == 1
    assert imported[0].name == 'exons.bed'
    history.delete(purge=True)

def test_import_dataset_from_library(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    library = gi.libraries.create('Test Library')
    library.upload_data("Some data")
    dataset_id = library.dataset_ids[0]
    gflow.datasets = {0: {'source': 'library', 'dataset_id': dataset_id, 'library_id': library.id,
                      'input_label': 'Exons'}}
    imported = gflow.import_datasets('datasets', gi, history)
    assert len(imported) == 1
    assert imported[0].name == 'Pasted Entry'
    library.delete()
    history.delete(purge=True)

def test_import_dataset_from_incorrect_source(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.datasets = {0: {'source': 'wrong', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'}}
    with pytest.raises(ValueError) as excinfo:
        gflow.import_datasets('datasets', gi, history)
    assert "Dataset source must be either 'local' or 'library'" in str(excinfo.value)
    history.delete(purge=True)

def test_import_dataset_wrong_data_group_type(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'}}
    with pytest.raises(ValueError) as excinfo:
        gflow.import_datasets('wrong_kind', gi, history)
    assert "Data group type must be 'datasets' or 'dataset_collection'" in str(excinfo.value)
    history.delete(purge=True)

def test_import_dataset_wrong_file(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/bad', 'input_label': 'Exons'}}
    with pytest.raises(IOError) as excinfo:
        gflow.import_datasets('datasets', gi, history)
    assert "Dataset file 'data/bad' does not exist" in str(excinfo.value)
    history.delete(purge=True)

def test_create_dataset_collection_list(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.dataset_collection = {
        'intput_label': 'label',
        'type': 'list',
        'datasets': {
            0: {
                'source': 'local',
                'dataset_file': 'data/exons.bed',
            },
            1: {
                'source': 'local',
                'dataset_file': 'data/SNPs.bed'
            }
        }
    }
    dataset_collection = gflow.create_dataset_collection(gi, history, 'DatasetList')
    assert dataset_collection.name == 'DatasetList'
    assert dataset_collection.collection_type == 'list'
    elements = dataset_collection.elements
    assert len(elements) == 2
    assert elements[0]['object']['name'] == 'exons.bed'
    assert elements[1]['object']['name'] == 'SNPs.bed'
    history.delete(purge=True)

def test_create_paired_dataset_collection(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.dataset_collection = {
        'intput_label': 'label',
        'type': 'list:paired',
        'datasets': {
            0: {
                'source': 'local',
                'dataset_file': 'data/exons.bed',
            },
            1: {
                'source': 'local',
                'dataset_file': 'data/SNPs.bed'
            }
        }
    }
    dataset_collection = gflow.create_dataset_collection(gi, history, 'DatasetList')
    assert dataset_collection.name == 'DatasetList'
    assert dataset_collection.collection_type == 'list:paired'
    elements = dataset_collection.elements
    assert len(elements) == 1
    assert elements[0]['object']['elements'][0]['object']['name'] == 'exons.bed'
    assert elements[0]['object']['elements'][1]['object']['name'] == 'SNPs.bed'
    history.delete(purge=True)

def test_create_dataset_collection_wrong_type(gflow, gi):
    history = gi.histories.create(gflow.history_name)
    gflow.dataset_collection = {
        'intput_label': 'label',
        'type': 'wrong',
        'datasets': {}
    }
    with pytest.raises(ValueError) as excinfo:
        gflow.create_dataset_collection(gi, history, 'DatasetList')
    assert "Dataset collection type must be 'list' or 'list:paired'" in excinfo.value
    history.delete(purge=True)

# def test_verify_runtime_parameters(gflow, gi):
#     workflow = gflow.import_workflow(gi)
#     missing_param = gflow.verify_runtime_params(workflow)
#     assert missing_param == ['lineNum']
#     workflow.delete()

def test_verify_no_runtime_params(gflow, gi):
    gflow.workflow = "workflows/select_sort.ga"
    workflow = gflow.import_workflow(gi)
    missing_param = gflow.verify_runtime_params(workflow)
    assert missing_param is None
    workflow.delete()

# def test_set_correct_runtime_params(gflow, gi):
#     workflow = gflow.import_workflow(gi)
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {
#                 'name': 'lineNum',
#                 'value': '10'
#             }
#         }
#     }
#     params = gflow.set_runtime_params(workflow)
#     assert params.values()[0] == {'lineNum': '10'}
#     workflow.delete()

# def test_set_incorrect_runtime_params(gflow, gi):
#     workflow = gflow.import_workflow(gi)
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {
#                 'name': 'wrong_name',
#                 'value': '10'
#             }
#         }
#     }
#     params = gflow.set_runtime_params(workflow)
#     assert params == {}
#     workflow.delete()

# def test_successful_workflow_with_runtime_params(gflow, gi):
#     gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'},
#                       1: {'source': 'local', 'dataset_file': 'data/SNPs.bed', 'input_label': 'Features'}}
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {
#                 'name': 'lineNum',
#                 'value': '10'
#             }
#         }
#     }
#     results, outputhist = gflow.run(temp_wf=True)
#     assert isinstance(results[0], wrappers.HistoryDatasetAssociation)
#     assert isinstance(outputhist, wrappers.History)
#     outputhist.delete(purge=True)

# def test_successful_workflow_with_library(gflow, gi):
#     gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'},
#                       1: {'source': 'local', 'dataset_file': 'data/SNPs.bed', 'input_label': 'Features'}}
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {
#                 'name': 'lineNum',
#                 'value': '10'
#             }
#         }
#     }
#     gflow.library_name = 'library_%s' % uuid.uuid4().hex
#     results, outputhist = gflow.run(temp_wf=True)
#     assert isinstance(results[0], wrappers.HistoryDatasetAssociation)
#     assert isinstance(outputhist, wrappers.History)
#     outputhist.delete(purge=True)
#     library = gi.libraries.list(name=gflow.library_name)[0]
#     library.delete()

# def test_workflow_run_missing_runtime_param(gflow, gi):
#     gflow.history_name = 'history_%s' % uuid.uuid4().hex
#     gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'},
#                       1: {'source': 'local', 'dataset_file': 'data/SNPs.bed', 'input_label': 'Features'}}
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {}
#         }
#     }
#     with pytest.raises(KeyError) as excinfo:
#         gflow.run(temp_wf=True)
#     assert "Missing value for 'value' key in runtime parameters" in str(excinfo.value)
#     workflow = gi.workflows.list("galaxy101-2015_avjasdvuweufwevw9wf (imported from API)")[0]
#     workflow.delete()
#     history = gi.histories.list(gflow.history_name)[0]
#     history.delete(purge=True)

def test_successful_workflow_no_runtime_params(gflow):
    gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Input Dataset'}}
    gflow.workflow = 'workflows/select_sort.ga'
    results, outputhist = gflow.run(temp_wf=True)
    assert isinstance(results[0], wrappers.HistoryDatasetAssociation)
    assert isinstance(outputhist, wrappers.History)
    outputhist.delete(purge=True)

# def test_workflow_missing_runtime_params(gflow, gi):
#     gflow.history_name = 'history_%s' % uuid.uuid4().hex
#     gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'},
#                       1: {'source': 'local', 'dataset_file': 'data/SNPs.bed', 'input_label': 'Features'}}
#     with pytest.raises(RuntimeError) as excinfo:
#         gflow.run(temp_wf=True)
#     assert "Missing runtime parameter" in str(excinfo.value)
#     workflow = gi.workflows.list("galaxy101-2015_avjasdvuweufwevw9wf (imported from API)")[0]
#     workflow.delete()
#     history = gi.histories.list(gflow.history_name)[0]
#     history.delete(purge=True)

# def test_successful_workflow_with_dataset_collection(gflow, gi):
#     gflow.datasets = {0: {'source': 'local', 'dataset_file': 'data/exons.bed', 'input_label': 'Exons'},
#                       1: {'source': 'local', 'dataset_file': 'data/SNPs.bed', 'input_label': 'Features'}}
#     gflow.runtime_params = {
#         'tool_0': {
#             'param_0': {
#                 'name': 'lineNum',
#                 'value': '10'
#             }
#         }
#     }
#     gflow.dataset_collection = {'input_label': '2 FASTQ Files',
#                                 'type': 'list',
#                                 'datasets': {
#                                     0: {
#                                         'source': 'local',
#                                         'dataset_file': 'data/Exons.bed'
#                                     },
#                                     1: {
#                                         'source': 'local',
#                                         'dataset_file': 'data/SNPs.bed'
#                                     }
#                                 }}
#     results, outputhist = gflow.run(temp_wf=True)
#     assert isinstance(results[0], wrappers.HistoryDatasetAssociation)
#     assert isinstance(outputhist, wrappers.History)
#     outputhist.delete(purge=True)
