import os
import config.config as config

parent_dir = os.path.dirname(os.path.dirname(__file__))

framework_dir = os.path.join(parent_dir, 'pyControl')
devices_dir   = os.path.join(parent_dir, 'devices')
config_dir    = os.path.join(parent_dir, 'config')
hwd_path      = os.path.join(config_dir, 'hardware_definition.py')

tasks_dir = config.tasks_dir if hasattr(config, 'tasks_dir') else os.path.join(parent_dir, 'tasks')
data_dir  = config.data_dir  if hasattr(config, 'data_dir')  else os.path.join(parent_dir, 'data')