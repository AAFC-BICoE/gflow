import logging

"""
Initialize logging
"""
logger = logging.getLogger('gflow')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('gflow.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                                 datefmt='%m/%d/%Y %I:%M:%S %p')
ch_formatter = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
fh.setFormatter(fh_formatter)
ch.setFormatter(ch_formatter)
logger.addHandler(ch)
logger.addHandler(fh)