#!/home/stephen/miniconda3/bin/python
###############################################################################
#
# file_open.py
# Stephen Zhao

import argparse
import os
import re
import subprocess
import sys
from typing import List, Optional

DEBUG = True

PROG_DESC_TEXT = "Opens the given file using an executable from a smart lookup scheme."

file_type_to_exe_map = {
  'local/directory': 'explorer.exe',
  'local/file/jpg': '/mnt/d/Program Files/IrfanView/i_view64.exe',
  'local/file/pdf': os.environ.get('BROWSER', 'chrome'),
  'local/file/png': '/mnt/d/Program Files/IrfanView/i_view64.exe',
  'web/something': os.environ.get('BROWSER', 'chrome')
}

# exe_to_arg_map = {
#   '/mnt/d/Program Files/IrfanView/i_view64.exe': 
# }

def debug(*args):
  if DEBUG:
    print(*args, file=sys.stderr)

def re_fullmatch_i(pattern: str, string: str):
  return re.fullmatch(pattern, string, flags=re.IGNORECASE)

def determine_resource_locality(resource_path: str) -> str:
  if resource_path.startswith('http://') \
      or resource_path.startswith('https://'):
    return 'web'
  else:
    return 'local'

def determine_resource_type(resource_path: str) -> str:
  locality = determine_resource_locality(resource_path)
  if locality == 'web':
    return 'web/something'
  elif locality == 'local':
    return determine_file_type(resource_path)

def determine_file_type(file_path: str) -> str:
  if re_fullmatch_i('.+\.jpe?g', file_path):
    return 'local/file/jpg'
  if re_fullmatch_i('.+\.pdf', file_path):
    return 'local/file/pdf'
  if re_fullmatch_i('.+\.png', file_path):
    return 'local/file/png'
  elif os.path.isdir(file_path):
    return 'local/directory'
  elif os.path.isfile(file_path):
    return 'local/file/unknown'
  else:
    return 'local/file/unknown_special'

def determine_exe(file_type: str) -> Optional[str]:
  if file_type == 'local/file/unknown':
    return None
  if file_type == 'local/file/unknown_special':
    return None
  else:
    return file_type_to_exe_map[file_type]

def main(argv: List[str]):
  arg_parser = argparse.ArgumentParser(description=PROG_DESC_TEXT)
  arg_parser.add_argument('file', type=str, help='the file to open')
  arg_parser.add_argument('exec', type=str, help='executable to override the default', nargs='?', default=None)

  args = arg_parser.parse_args(argv[1:])
  
  file_type = determine_file_type(args.file)
  exe = determine_exe(file_type)
  if not exe:
    arg_parser.print_usage()
    exit(1)
  debug('exe:', exe)
  debug('pwd:', os.getcwd())
  debug('file:', args.file)
  debug('file_type:', file_type)
  pid = subprocess.Popen([exe, args.file]).pid
  debug('pid:', pid)

if __name__ == '__main__':
  main(sys.argv)