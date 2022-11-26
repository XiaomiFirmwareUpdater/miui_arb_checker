#!/usr/bin/env python3
"""
MIUI Anti-Rollback checker
"""
import codecs
import re
import tarfile
from zipfile import ZipFile
from os import makedirs, path
from shutil import rmtree
from sys import argv
from glob import glob


def check_file():
    """
    check if file exists
    """
    file_type = ''
    if len(argv) < 2:
        print("No file was provided!\n"
              "Usage: python3 miui_arb_checker.py <file_to_check>")
        exit(0)
    if not path.isfile(argv[1]):
        print("The file provided does not exist!")
        exit(0)
    if '.zip' in argv[1]:
        file_type = 'zip'
    elif '.tgz' in argv[1]:
        file_type = 'tgz'
    elif '.sh' in argv[1] or '.bat' in argv[1]:
        file_type = 'sh'
    elif 'xbl' in argv[1]:
        file_type = 'xbl'
    else:
        print('The file to check must be Recovery / Fastboot ROM, XBL file, '
              'or .sh flashing script!')
        exit(0)
    return file_type


def extract_zip(file):
    """
    extract xbl file from recovery rom
    :param file: miui zip
    """
    with ZipFile(file, 'r') as zip_file:
        files = [i for i in zip_file.namelist()
                 if i.startswith('firmware-update/xbl.')]
        if not files:
            print("There's no xbl files to check in this ZIP!")
            exit(0)
        print('xbl file extracted successfully.')
        zip_file.extractall(path="tmp", members=files)


def extract_tar(file):
    """
    extract flashing script from fastboot rom
    :param file: miui tgz
    """
    with tarfile.open(file, 'r') as tar_file:
        files = [i for i in tar_file.getnames() if 'flash_all.sh' in i][0]
        
        import os
        
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar_file, "tmp", members=[tar_file.getmember(files)])
        print('flashing script extracted successfully.')


def get_arb_number(xbl):
    """
    check the current ARB number in xbl strings
    :param xbl: bootloader file
    """
    with open(xbl, "rb") as binary_file:
        data = codecs.decode(binary_file.read(), 'ascii', errors='ignore')
    try:
        arb = [i for i in re.findall(r"0000000[0-9]00000000", data)
               if i != '0000000000000000'][0]
    except IndexError:
        arb = []
    if not arb:
        print('No ARB detected!')
    else:
        print('ARB index is: ' + arb.replace('0', ''))
        print('Note: sometimes this can be inaccurate!\n'
              'Be sure to check curring anti number using fastboot or from XDA/MIUI forum.')


def check_xbl(file_type):
    """
    check anti-rollback index in bootloader
    """
    file_path = ''
    if file_type == 'zip':
        file_path = "tmp/firmware-update/xbl.*"
    elif file_type == 'xbl':
        file_path = "xbl.*"
    for xbl in glob(file_path):
        get_arb_number(xbl)


def read_arb_number(file):
    """
    read the current ARB number from shell flashing script
    :param file: flashing script file
    """
    with open(file, 'r') as script:
        arb = [i for i in script if 'CURRENT_ANTI_VER=' in i][0]
        if not arb:
            print('No ARB detected!')
        else:
            print('ARB index is: ' + arb.split('=')[1])


def check_flash_script(file_type):
    """
    check anti-rollback index in fastboot flashing script
    """
    file_path = ''
    if file_type == 'tgz':
        file_path = "tmp/*/flash_all.sh"
    elif file_type == 'sh':
        file_path = "flash_*.sh"
    for file in glob(file_path):
        read_arb_number(file)


def main():
    """
    check anti-rollback index in xbl file
    """
    file_type = check_file()
    makedirs("tmp", exist_ok=True)
    file = argv[1]
    if file_type == 'zip':
        print('Checking ARB from Recovery ROM')
        extract_zip(file)
        check_xbl(file_type)
    elif file_type == 'tgz':
        print('Checking ARB from Fastboot ROM')
        extract_tar(file)
        check_flash_script(file_type)
    elif file_type == 'sh':
        print('Checking ARB from Fastboot Flashing Script')
        check_flash_script(file_type)
    elif file_type == 'xbl':
        print('Checking ARB from XBL file')
        check_xbl(file_type)
    else:
        print("Something went wrong!")
    rmtree("tmp/")


if __name__ == '__main__':
    main()
