from gflow.GalaxyCMDWorkflow import GalaxyCMDWorkflow
import pytest


def test_config_file_missing_required_parameter_is_rejected(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("empty: something")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    with pytest.raises(KeyError) as excinfo:
        GalaxyCMDWorkflow.init_from_config_file(tmp_config)
    assert 'Missing required parameter: \'galaxy_url\'' in str(excinfo.value)


def test_config_file_with_empty_value_for_required_param_is_rejected(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("galaxy_url: ")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    with pytest.raises(ValueError) as excinfo:
        GalaxyCMDWorkflow.init_from_config_file(tmp_config)
    assert 'Missing value for required parameter: galaxy_url' in str(excinfo.value)


def test_config_file_with_no_empty_files_accepted(tmpdir):
    p = tmpdir.mkdir("sub").join("tmp_config.yml")
    p.write("galaxy_url: something\n"
            "galaxy_key: something\n"
            "library_name: something\n"
            "history_name: something\n"
            "workflow_source: something\n"
            "workflow: something\n")
    tmp_config = str(p.dirpath() + "/tmp_config.yml")
    gflow = GalaxyCMDWorkflow.init_from_config_file(tmp_config)
    assert gflow.galaxy_url == "something"
    assert gflow.galaxy_key == "something"
    assert gflow.library_name == "something"
    assert gflow.history_name == "something"
    assert gflow.workflow_source == "something"
    assert gflow.workflow == "something"
