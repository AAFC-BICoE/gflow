import getopt
import ConfigParser
import sys


class Config(object):

    def __init__(self):

        configfile = self.parse_options()
        config = ConfigParser.RawConfigParser()
        config.read(configfile)

        self.galaxy_url = config.get('galaxy', 'galaxy_url')
        self.galaxy_key = config.get('galaxy', 'galaxy_key')

        self.new_library = config.get('library', 'new')
        self.library = config.get('library', 'library')

        self.dataset_src = config.get('input', 'dataset_src')
        if self.dataset_src not in ['local', 'url', 'galaxyfs']:
            print >> sys.stderr, "ERROR: Accepted dataset sources are: local, url, or galaxyfs"
            sys.exit(1)
        self.num_datasets = config.getint('input', 'num_datasets')
        self.datasets = []
        self.labels = []
        try:
            for i in range(0, self.num_datasets):
                self.datasets.append(config.get('input', "data" + str(i)))
                self.labels.append(config.get('input', "label" + str(i)))
        except ConfigParser.NoOptionError as e:
            print >> sys.stderr, "ERROR: The number of datasets or labels provided does not match the number required"
            print >> sys.stderr, e
            sys.exit(1)

        self.outputhist = config.get('output', 'output_history_name')

        self.workflow_src = config.get('workflow', 'source')
        if self.workflow_src not in ['local', 'shared', 'id']:
            print >> sys.stderr, "ERROR: Accepted dataset sources are: local or shared"
            sys.exit(1)
        self.workflow = config.get('workflow', 'workflow')

        self.num_tools = config.getint('tool_params', 'num_tools')
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
            print >> sys.stderr, e
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
                print >> sys.stderr, "ERROR: Opening config file %s" % configfile
                print >> sys.stderr, e
                sys.exit(1)
        elif not sys.stdin.isatty():
            instream = sys.stdin
        else:
            print >> sys.stderr, "ERROR: Please provide a config file"
            self.print_usage(sys.stderr)
            sys.exit(1)
        instream.close()
        return configfile