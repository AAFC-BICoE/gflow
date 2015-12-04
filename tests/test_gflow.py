from gflow.gflow import *
import pytest

@pytest.fixture
def gi_fix():
    galaxy_url = os.environ.get("GALAXY_URL", None)
    galaxy_key = os.environ.get("GALAXY_KEY", None)
    gi = GalaxyInstance(galaxy_url, galaxy_key)
    return gi

def test_config_file_with_empty_value_rejected(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("empty: ")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    with pytest.raises(RuntimeError):
        GFlow(tmp_config)

def test_config_file_with_no_empty_files_accepted():
    assert GFlow('tests/config/config0.yml')

# def test_error_on_no_galaxy_credentials(self, tmpdir):
#     if 'GALAXY_URL' in os.environ:
#         os.environ.pop('GALAXY_URL')
#     if 'GALAXY_KEY' in os.environ:
#         os.environ.pop('GALAXY_KEY')
#     p = tmpdir.mkdir("sub").join("tmp_config.yml")
#     p.write("workflow: something")
#     tmp_config = str(p.dirpath() + "/tmp_config.yml")
#     gflow = GFlow(tmp_config)
#     with pytest.raises(ValueError):
#         gflow.run_workflow()

def test_import_workflow_from_local_file(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    assert gflow.import_workflow(gi)

def test_import_workflow_with_bad_file_name(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    gflow.cfg['workflow']['workflow'] = "doesn't exist"
    with pytest.raises(IOError):
        gflow.import_workflow(gi)

def test_get_workflow_from_id(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    gflow.cfg['workflow']['workflow_src'] = 'id'
    workflows = gi.workflows.list()
    id = workflows[0].id
    gflow.cfg['workflow']['workflow'] = id
    assert gflow.import_workflow(gi)

def test_invalid_workflow_source(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    gflow.cfg['workflow']['workflow_src'] = 'wrong'
    with pytest.raises(ValueError):
        gflow.import_workflow(gi)

def test_data_from_local_files(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    library = gi.libraries.create(gflow.cfg['library'])
    assert gflow.import_data(library)

def test_import_data_with_bad_file_name(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    library = gi.libraries.create(gflow.cfg['library'])
    gflow.cfg['input']['datasets']['dataset_0']['data'] = "doesn't exist"
    with pytest.raises(IOError):
        gflow.import_data(library)

def test_invalid_data_source(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    library = gi.libraries.create(gflow.cfg['library'])
    gflow.cfg['input']['dataset_src'] = "unsupported"
    with pytest.raises(ValueError):
        gflow.import_data(library)

def test_set_tool_params_success(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    gi = gi_fix
    wf = gflow.import_workflow(gi)
    assert gflow.set_tool_params(wf)

def test_successful_workflow_run(gi_fix):
    gflow = GFlow('tests/config/config0.yml')
    assert gflow.run_workflow()