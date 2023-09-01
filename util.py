
import os
import glob
import sys
import shutil


def delete_files_with_extension(extensions):
    # Find files by extension
    for extension in extensions:
        files = glob.glob(f"*.{extension}")

        #Remove files found
        for file in files:
            os.remove(file)

def unlink_file(file_name):
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
    except OSError as err:
        print(f"Unexpected {err=}, {type(err)=}")


def get_terraform_bin(bin):
    try:
        bin_path = shutil.which(bin)
    except shutil.Error as err:
        print(f"Unexpected {err=}, {type(err)=}")
        bin_path = None
    return bin_path

