import getopt
import ConfigParser
import sys
import logging


class Config(object):

    def __init__(self, configfile=None):

        self.logger = logging.getLogger('gflow.Config')

        self.logger.info("Reading config file")
        if not configfile:
            configfile = self.parse_options()

        config = ConfigParser.RawConfigParser()
        config.read(configfile)

        try:

            self.logger.debug("Storing Galaxy credentials")
            self.galaxy_url = config.get('galaxy', 'galaxy_url')
            self.galaxy_key = config.get('galaxy', 'galaxy_key')

            self.logger.debug("Storing new library name")
            self.library = config.get('library', 'library')

            self.logger.debug("Storing input datasets")
            self.dataset_src = config.get('input', 'dataset_src')
            if self.dataset_src not in ['local', 'url', 'galaxyfs']:
                self.logger.error("Accepted dataset sources are local, url, or galaxyfs")
                sys.exit(1)
            self.num_datasets = config.getint('input', 'num_datasets')
            self.datasets = []
            self.labels = []
            for i in range(0, self.num_datasets):
                self.datasets.append(config.get('input', "data_" + str(i)))
                self.labels.append(config.get('input', "label_" + str(i)))
            input_options = config.options('input')
            if len(input_options) > 2 + 2 * self.num_datasets:
                self.logger.error("More datasets given than 'num_datsets' specified")
                sys.exit(1)

            self.logger.debug("Storing output history name")
            self.outputhist = config.get('output', 'output_history_name')

            self.logger.debug("Storing workflow source and name")
            self.workflow_src = config.get('workflow', 'source')
            if self.workflow_src not in ['local', 'shared', 'id']:
                self.logger.error("Accepted dataset sources are local or shared")
                sys.exit(1)
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
            sys.exit(1)

        self.logger.debug("Check for empty values")
        self.empty_value_check(config)

    def empty_value_check(self, config):
        for section in config.sections():
            for option in config.options(section):
                value = config.get(section, option)
                if not value:
                    self.logger.error("Missing a value for required '%s' option" % option)
                    sys.exit(1)
        return 0

    @staticmethod
    def print_usage(outstream):
        usage = ("Usage: gflow.py [options] config.txt\n"
                 "  Options:\n"
                 "    -h|--help           print this help message and exit")
        print >> outstream, usage

    def parse_options(self):
        outstream = sys.stdout
        optstr = "h:"
        longopts = ["help"]
        try:
            (options, args) = getopt.getopt(sys.argv[1:], optstr, longopts)
        except getopt.GetoptError as e:
            self.logger.error(e)
            sys.exit(1)
        for key, value in options:
            if key in ("-h", "--help"):
                self.print_usage(outstream)
                sys.exit(0)
            else:
                pass
        configfile = None
        if len(args) > 0:
            configfile = args[0]
            try:
                instream = open(configfile, "r")
            except IOError as e:
                self.logger("Cannot open config file %s" % configfile)
                self.logger(e)
                sys.exit(1)
        elif not sys.stdin.isatty():
            instream = sys.stdin
        else:
            self.logger.error("Please provide a config file")
            self.print_usage(sys.stderr)
            sys.exit(1)
        instream.close()
        return configfile
