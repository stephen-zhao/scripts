#!/home/stephen/miniconda3/bin/python
###############################################################################
#
# mklink.py
# Stephen Zhao

import argparse
import os
import sys
from typing import List

DEBUG = True

PROG_DESC_TEXT = "Creates a new shortcut link to an internet URL."

LINK_TEXT_TEMPLATE = """<html><body><script type="text/javascript">
window.location.href = "{}";
</script></body></html>
"""

def debug(*msg) -> None:
  if DEBUG:
    print("[DBUG][mklink]", *msg, file=sys.stderr)

def error(*msg) -> None:
  print("[ERRO][mklink]", *msg, file=sys.stderr)


def main(argv: List[str]):
  arg_parser = argparse.ArgumentParser(description=PROG_DESC_TEXT)
  arg_parser.add_argument('out', type=str, help='the name of the link file')
  arg_parser.add_argument('url', type=str, help='the url that the file points to')
  arg_parser.add_argument('-v', '--verbose', action='store_true', default=False)

  args = arg_parser.parse_args(argv[1:])

  def info(*msg):
    if args.verbose:
      print("[INFO][mklink]", *msg)
  
  if not args.out.endswith('.html') or\
     not args.out.endswith('.htm'):
    args.out += '.html'

  try:
    with open(args.out, 'w') as file:
      file.write(LINK_TEXT_TEMPLATE.format(args.url))
  except:
    error('something went wrong when writing to file {}'.format(args.out))
  info('\n  link\n    {}\n  created pointing at url\n    {}\n'.format(args.out, args.url))

if __name__ == '__main__':
  main(sys.argv)
