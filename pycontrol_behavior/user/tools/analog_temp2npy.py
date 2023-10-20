import os
import numpy as np


def find_files_with_extension(folder_path, extension):
    """Return paths for all files with specified file extension in specified
    folder and sub-folders"""
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))
    return file_paths


def tempfile2npy(file_path):
    """Convert a single temp file to a .npy file."""
    file_type = file_path.split(".")[-2]
    path_stem = file_path.rsplit(".", 2)[0]
    with open(file_path, "rb") as f:
        if file_type == "time":  # Timestamp file
            times = np.frombuffer(f.read(), dtype="float64")
            np.save(path_stem + ".time.npy", times)
        else:  # Data samples file.
            data_type = file_type[-1]
            data = np.frombuffer(f.read(), dtype=data_type)
            np.save(path_stem + ".data.npy", data)
    os.remove(file_path)


def all_tempfile2numpy(folder_path):
    """Convert all .temp files in specified folder to .npy"""
    file_paths = find_files_with_extension(folder_path, ".temp")
    for file_path in file_paths:
        tempfile2npy(file_path)


if __name__ == "__main__":
    # Convert all temp files in data folder to npy.
    print("Converting .temp files to .npy")
    try:
        data_path = os.path.join("..", "data")
        all_tempfile2numpy(data_path)
        print("\nFiles converted successfully.")
    except Exception as e:
        print("\nUnable to convert files.")
        print(e)
    input("\nPress enter to close.")
