import logging
from oslo_config import cfg
import sys

OPTS = [
        cfg.StrOpt('log_file',default='/var/log/qyceilometer/qyceilometer.log',
            help=('(required) the global log')),
        cfg.BoolOpt('debug',default=False,
            help=('(optional) the level of log')),
]

cfg.CONF.register_opts(OPTS, group='logging')

def prepare_service():

	argv = sys.argv
	cfg.CONF(default_config_files = argv[1].split('=')[1:])

	logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
	 	datefmt='%a, %d %b %Y %H:%M:%S',
	 	level=logging.DEBUG, # if cfg.CONF.logging.debug else logging.ERROR,
	 	filename=cfg.CONF.logging.log_file,
	 	filemode='a')
		