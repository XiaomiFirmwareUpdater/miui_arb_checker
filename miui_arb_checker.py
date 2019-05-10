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
    if 'zip' in argv[1]:
        file_type = 'zip'
    elif 'tgz' in argv[1]:
        file_type = 'tgz'
    else:
        print('ROM to check must be ZIP or TAR only!')
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
        for i in glob("*/flash_all.sh"):
            tar_file.extractall('tmp', members=[tar_file.getmember(i)])
            print('flashing script extracted successfully.')


def check_xbl():
    """
    check anti-rollback index in bootloader
    """
    for xbl in glob("tmp/firmware-update/xbl.*"):
        with open(xbl, "rb") as binary_file:
            data = codecs.decode(binary_file.read(), 'ascii', errors='ignore')
            arb = [i for i in re.findall(r"0000000[0-9]00000000", data)
                   if i != '0000000000000000'][0]
            if not arb:
                print('No ARB detected!')
            else:
                print('ARB index is: ' + arb.replace('0', ''))
                print('Note: sometimes this can be inaccurate!\n'
                      'Be sure to check using fastboot or XDA/MIUI forum')


def check_flash_script():
    """
    check anti-rollback index in fastboot flashing script
    """
    for file in glob("tmp/*/flash_all.sh"):
        with open(file, 'r') as script:
            arb = [i for i in script if 'CURRENT_ANTI_VER=' in i][0]
            if not arb:
                print('No ARB detected!')
            else:
                print('ARB index is: ' + arb.split('=')[1])


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
        check_file()
    elif file_type == 'tgz':
        print('Checking ARB from Fastboot ROM')
        extract_tar(file)
        check_flash_script()
    else:
        print("Something went wrong!")
    rmtree("tmp/")


if __name__ == '__main__':
    main()
