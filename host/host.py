import kick
import pyboard as pb
import os

#port = 'COM23'
#board = pb.Pyboard(port)
#board.enter_raw_repl()
#pyControl_dir = 'C:\\Users\\Thomas\\Documents\\Dropbox\\Hardware development\\pyControl\\pyControl'
#tasks_dir = 'C:\\Users\\Thomas\\Documents\\Dropbox\\Hardware development\\pyControl\\examples'

def transfer_file(board, file_path, target_path = None):
    '''Copy a file into the root directory of the pyboard.'''
    if not target_path:
        target_path = os.path.split(file_path)[-1]
    data = open(file_path).read()
    board.exec("tmpfile = open('{}','w')".format(target_path))
    board.exec("tmpfile.write({data})".format(data=repr(data)))
    board.exec('tmpfile.close()')

def transfer_folder(board, folder_path, target_folder = None, file_type = 'all'):
    '''Copy a folder into the root directory of the pyboard.  Folders that
    contain subfolders will not be copied successfully.  To copy only files of
    a specific type, change the file_type argument to the file suffix (e.g. 'py').'''
    if not target_folder:
        target_folder = os.path.split(folder_path)[-1]
    files = os.listdir(folder_path)
    if file_type != 'all':
        files = [f for f in files if f.split('.')[-1] == file_type]
    try:
        board.exec('import os;os.mkdir({})'.format(repr(target_folder)))
    except pb.PyboardError:
        pass # Folder already exists.
    for f in files:
        file_path = os.path.join(folder_path, f)
        target_path = target_folder + '/' + f
        transfer_file(board, file_path, target_path)



