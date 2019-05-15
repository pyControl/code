import os
_base_path = os.path.dirname(__file__)
_user_files = [f.split('.')[0] for f in os.listdir(_base_path) if 'init' not in f]
for _user_file in _user_files:
    exec('from api.user_classes.{} import *'.format(_user_file))
