import ConfigParser
import logging
import os


class Config(object):
    """
    Read a config file and saves its contents.

    Args:
        configfile (str): The location of the configuration file.
    """

    def __init__(self, configfile):

        self.logger = logging.getLogger('gflow.Config')
        self.logger.info("Reading config file")
        config = ConfigParser.RawConfigParser()
        config.read(configfile)

        try:

            self.logger.debug("Storing Galaxy credentials")
            self.galaxy_url = os.environ.get("GALAXY_URL", None)
            self.galaxy_key = os.environ.get("GALAXY_KEY", None)
            if not self.galaxy_key or not self.galaxy_url:
                self.logger.error("GALAXY_URL and/or GALAXY_KEY environment variable(s) not set")

            self.logger.debug("Storing new library name")
            self.library = config.get('library', 'library')

            self.logger.debug("Storing input datasets")
            self.dataset_src = config.get('input', 'dataset_src')
            if self.dataset_src not in ['local', 'url', 'galaxyfs']:
                self.logger.error("Accepted dataset sources are local, url, or galaxyfs")
            self.num_datasets = config.getint('input', 'num_datasets')
            self.datasets = []
            self.labels = []
            for i in range(0, self.num_datasets):
                self.datasets.append(config.get('input', "data_" + str(i)))
                self.labels.append(config.get('input', "label_" + str(i)))
            input_options = config.options('input')
            if len(input_options) > 2 + 2 * self.num_datasets:
                self.logger.error("More datasets given than 'num_datsets' specified")

            self.logger.debug("Storing output history name")
            self.outputhist = config.get('output', 'output_history_name')

            self.logger.debug("Storing workflow source and name")
            self.workflow_src = config.get('workflow', 'source')
            if self.workflow_src not in ['local', 'shared', 'id']:
                self.logger.error("Accepted workflow sources are local, id, or shared")
            self.workflow = config.get('workflow', 'workflow')

            self.logger.debug("Storing tool parameters")
            self.num_tools = config.getint('tool_params', 'num_tools')
            if self.num_tools:
                self.step_ids = []
                self.num_tool_params = []
                self.tool_params = []
                for i in range(0, self.num_tools):
                    self.num_tool_params.append(config.getint('tool_params', "num_params_" + str(i)))
                    self.step_ids.append(config.get('tool_params', 'tool_' + str(i)))
                    temp_dict = {}
                    for j in range(0, self.num_tool_params[i]):
                        param_label = config.get("tool_params", "param_label_" + str(i) + "-" + str(j))
                        param_value = config.get("tool_params", "param_" + str(i) + "-" + str(j))
                        temp_dict[param_label] = param_value
                    self.tool_params.append(temp_dict)

        except ConfigParser.NoOptionError as e:
            self.logger.error("Missing required option(s) in config file")
            self.logger.error(e)

        self.logger.debug("Checking for empty values")
        self.empty_value_check(config)

    def empty_value_check(self, config):
        """
        Check the config file for options with no value.

        Args:
            config (RawConfigParser): The Config object to check.
        Returns:
            True if successful, False otherwise.
        """
        result = True
        for section in config.sections():
            for option in config.options(section):
                value = config.get(section, option)
                if not value:
                    self.logger.error("Missing a value for required option '%s'" % option)
                    result = False
        return result
