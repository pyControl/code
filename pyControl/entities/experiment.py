# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrol.entities.experiment

"""

import logging
import pycontrol

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

logger = logging.getLogger(__name__)


class Experiment(object):
    'Class used to hold information about an experiment'

    def __init__(self, name, start_date, subjects, task, set_variables=None,
                 persistent_variables=None, folder=None, transfer_folder=None,
                 summary_data=None):
        ''' Arguments:
        subjects : dict specifying the ID of the subject run in each box.
        set_variables:  dict specifying variables whose values should be
                        modified from defaults in script.  A dict of box numbers
                        and values can be provided as a variable to set variable
                        differently for each box.
        persistant_variables:  list of variables whose values should be persistant
                               from session to session.
        folder:  name of data folder, defaults to start_date + name.
        '''
        self.name = name
        self.start_date = start_date
        self.subjects = subjects
        self.task = task
        self.set_variables = set_variables
        self.persistent_variables = persistent_variables
        self.n_subjects = len(self.subjects.keys())
        self.transfer_folder = transfer_folder
        self.summary_data = summary_data
        if folder:
            self.folder = folder
        else:
            self.folder = start_date + '-' + name