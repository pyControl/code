import os

import pycontrol

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------

# djb2 hashing algorithm used to check integrity of transfered files.

djb2_file_source_code = \
    """def djb2_file(file_path):
        with open(file_path, 'r') as f:
            h = 5381
            while True:
                c = f.read(1)
                if not c:
                    break
                h = ((h * 33) + ord(c)) & 0xFFFFFFFF
        return h
    """


def djb2_file(file_path):
    with open(file_path, 'r') as f:
        h = 5381
        while True:
            c = f.read(1)
            if not c:
                break
            h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h


# Used on pyboard to remove directories or files.

rm_dir_or_file_source_code = \
    """def rm_dir_or_file(i):
        try:
            os.remove(i)
        except OSError:
            os.chdir(i)
            for j in os.listdir():
                rm_dir_or_file(j)
            os.chdir('..')
            os.rmdir(i)
    """


def rm_dir_or_file(i):
    try:
        os.remove(i)
    except OSError:
        os.chdir(i)
        for j in os.listdir():
            rm_dir_or_file(j)
        os.chdir('..')
        os.rmdir(i)


# Used on pyboard to clear filesystem.

reset_pyb_filesystem_source_code = \
    """def reset_pyb_filesystem():
        os.chdir('/flash')
        for i in os.listdir():
            if i not in ['System Volume Information', 'boot.py']:
                rm_dir_or_file(i)
    """


def reset_pyb_filesystem():
    os.chdir('/flash')
    for i in os.listdir():
        if i not in ['System Volume Information', 'boot.py']:
            rm_dir_or_file(i)
