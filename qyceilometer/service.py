import logging
from oslo_config import cfg

def prepare_service(log_files, config_files):
	logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
	 	datefmt='%a, %d %b %Y %H:%M:%S',
	 	level=logging.DEBUG,
	 	filename=log_files,
	 	filemode='w')
	cfg.CONF(default_config_files = config_files)