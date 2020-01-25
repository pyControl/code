import os
import json

# Default paths.

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Top level pyControl folder.

dirs = {
        'config'      : os.path.join(top_dir, 'config'),
        'framework'   : os.path.join(top_dir, 'pyControl'),
        'devices'     : os.path.join(top_dir, 'devices'),
        'tasks'       : os.path.join(top_dir, 'tasks'), 
        'experiments' : os.path.join(top_dir, 'experiments'),
        'data'        : os.path.join(top_dir, 'data')
        }

# User paths - When paths.py is imported on opening GUI, load any 
# saved user paths and update the dirs dict.

def update_paths(user_paths):    
    for name, path in user_paths.items():
        if os.path.exists(path):
            dirs[name] = path

json_path = os.path.join(dirs['config'], 'user_paths.json')
if os.path.exists(json_path):
    with open(json_path,'r') as f:
        user_paths = json.loads(f.read())
        update_paths(user_paths)