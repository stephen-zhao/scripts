#!/home/stephen/miniconda3/bin/python
###############################################################################
# Author: Stephen Zhao
# App: dfregex_bulk_rename (rebrn)
# Version: v0.1
# Last modified: 2019-12-21
# Description: Renames files by substituting a search pattern with a
#      replacement pattern, with datetime formatting and regex support.

import argparse
from datetime import date, time, datetime
import os
from pathlib import Path
import re
import sys
from typing import *

IS_DEBUG = True

def debug(*args):
    if IS_DEBUG:
        print('[DEBUG]', *args)

#TODO: extract into its own package and ship!
class DatetimeMatcher:

    weekdays_abbr = [date(2019,12,22+i).strftime('%a') for i in range(7)]
    weekdays = [date(2019,12,22+i).strftime('%A') for i in range(7)]
    months_abbr = [date(2019,i,1).strftime('%b') for i in range(1, 13)]
    months = [date(2019,i,1).strftime('%B') for i in range(1, 13)]
    am_pm = [time(10).strftime('%p'), time(20).strftime('%p')]

    format_code_to_re = {
        r'%a': '({})'.format('|'.join(weekdays_abbr)),
        r'%A': '({})'.format('|'.join(weekdays)),
        r'%w': r'([0-6])',
        r'%d': r'(0[1-9]|[12][0-9]|3[01])',
        r'%b': '({})'.format('|'.join(months_abbr)),
        r'%B': '({})'.format('|'.join(months)),
        r'%m': r'(0[1-9]|1[0-2])',
        r'%y': r'([0-9]{2})',
        r'%Y': r'([0-9]{4})',
        r'%H': r'([01][0-9]|2[0-3])',
        r'%I': r'(0[1-9]|1[0-2])',
        r'%p': '({})'.format('|'.join(am_pm)),
        r'%M': r'([0-5][0-9])',
        r'%S': r'([0-5][0-9])',
        r'%f': r'([0-9]{6})'
        #TODO: finish adding all datetime formats
    }

    def supported_format_codes(self) -> List[str]:
        return self.__class__.format_code_to_re.keys()

    def get_regex_from_format_code(self, format_code) -> List[str]:
        return self.__class__.format_code_to_re[format_code]

    # Generates regexes for format codes, otherwise just spits out the character
    def _get_regex_parts(self, dfregex: str) -> Generator[str, None, None]:
        i = 0
        while i < len(dfregex):
            # If past the point at which a legal format code can exist,
            # just yield the existing character and go to the next.
            if i >= len(dfregex) - 1:
                yield dfregex[i]
                i += 1
            # Otherwise, check for a potential format code
            else:
                potential_format_code = dfregex[i:i+2]
                # If the characters at this i form a supported format code,
                # then yield the regex for that format code
                # and skip the next character.
                if potential_format_code in self.supported_format_codes():
                    yield self.get_regex_from_format_code(potential_format_code)
                    i += 2
                # Otherwise, just yield the existing character
                # and go to the next.
                else:
                    yield dfregex[i]
                    i += 1

    # Extracts the regex string from the datetime format augmented regex
    def get_regex(self, dfregex: str) -> Tuple[Dict[str, int], str]:
        return ''.join(self._get_regex_parts(dfregex))

    def get_format_codes_and_group_indices(self, dfregex: str) -> Tuple[List[str], List[int]]:
        codes = []
        indices = []
        index = 1 # start at 1 because index 0 is always the entire match
        for i in range(len(dfregex) - 1):
            if dfregex[i] == '(':
                if i > 0 and dfregex[i-1] == '\'':
                    continue
                if i < len(dfregex) - 2 and dfregex[i+1] == '?':
                    continue
                index += 1
            elif dfregex[i:i+2] in self.supported_format_codes():
                codes.append(dfregex[i:i+2])
                indices.append(index)
                index += 1
            else:
                pass
        return (codes, indices)

    def extract_datetime(self, search_dfregex: str, text: str) -> Optional[datetime]:
        search_regex = self.get_regex(search_dfregex)
        (codes, indices) = self.get_format_codes_and_group_indices(search_dfregex)
        match = re.match(search_regex, text)
        if not match:
            return None
        datetime_groups = list(map(lambda x: x[1], filter(lambda x: x[0]+1 in indices, enumerate(match.groups()))))
        datetime_string = '#'.join(datetime_groups)
        format_string = '#'.join(codes)
        try:
            parsed_datetime = datetime.strptime(datetime_string, format_string)
        except ValueError:
            return None
        return parsed_datetime

    def sub(self, search_dfregex: str, replacement_dfregex: str, text: str) -> str:
        search_regex = self.get_regex(search_dfregex)
        (codes, indices) = self.get_format_codes_and_group_indices(search_dfregex)
        # Substitute the string, regex-wise, leaving datetime formatters in place
        subbed_text_with_datetime_format = re.sub(search_regex, replacement_dfregex, text)
        # Get the datetime
        match = re.match(search_regex, text)
        if not match:
            return text
        datetime_groups = list(map(lambda x: x[1], filter(lambda x: x[0]+1 in indices, enumerate(match.groups()))))
        datetime_string = '#'.join(datetime_groups)
        format_string = '#'.join(codes)
        try:
            parsed_datetime = datetime.strptime(datetime_string, format_string)
        except ValueError:
            return text
        return parsed_datetime.strftime(subbed_text_with_datetime_format)


# Prints a neat table
# shamelessly copied, courtesy of u/ParalysedBeaver, from:
# https://www.reddit.com/r/inventwithpython/comments/455qgj/automate_the_boring_stuff_chapter_6_table_printer/d3f5l3e/
def printTable(inputList: List[str]) -> None:
    # initialize the list "colWidths" with zeroes equal to the length of the input list
    colWidths = [0] * len(inputList)

    # iterate over the input list to find the longest word in each inner list
    # if its larger than the current value, set it as the new value
    for i in range(len(inputList)):
        for j in range(len(inputList[i])):
            if len(inputList[i][j]) > colWidths[i]:
                colWidths[i] = len(inputList[i][j])

    # assuming each inner list is the same length as the first, iterate over the input list
    # printing the x value from each inner list, right justifed to its corresponding value
    # in colWidths
    for x in range(len(inputList[0])):
        for y in range(len(inputList)):
            print(inputList[y][x].rjust(colWidths[y]), end = ' ')
        print('')

def parse_args(args: List[str]) -> any:
    argparser = argparse.ArgumentParser(
        description="Renames files by substituting a search pattern with a replacement \
            pattern, with datetime formatting and regex support.")
    argparser.add_argument('directory')
    argparser.add_argument('search_pattern')
    argparser.add_argument('replacement_pattern')
    return argparser.parse_args(args)

def main(args):
    # Parse arguments
    args = parse_args(args)

    # Get path to directory
    path_to_directory = Path(args.directory)

    # Handle directory path errors
    if path_to_directory.is_file():
        print("File input is still unsupported")
        exit(2)
    if not path_to_directory.is_dir():
        print("Invalid directory or file")
        exit(3)

    # Get list of files in directory
    pre_rename_files = list(filter(lambda f: (path_to_directory / f).is_file(),
                        os.listdir(str(path_to_directory))))

    # Create a DatetimeMatcher to match regex with datetime formatting
    dtmatcher = DatetimeMatcher()

    # Generate new file names
    final_pre_rename_files = []
    final_post_rename_files = []
    for pre_rename_file in pre_rename_files:
        post_rename_file = dtmatcher.sub(args.search_pattern, args.replacement_pattern, pre_rename_file)
        if pre_rename_file != post_rename_file:
            final_pre_rename_files.append(pre_rename_file)
            final_post_rename_files.append(post_rename_file)

    # Get final length of files
    num_final_files = len(final_pre_rename_files)

    # Generate mapping
    files_oldtonew = dict((final_pre_rename_files[i], final_post_rename_files[i]) for i in range(num_final_files))

    # Make display table
    table_data = [final_pre_rename_files, ['-->' for i in range(num_final_files)], final_post_rename_files]

    # Early exit if no files to be renamed
    if num_final_files == 0:
        print("No renames to be done!")
        print("Exiting...")
        exit()

    # Display all files and pending rename results
    print("Pending renames to be done: ")
    printTable(table_data)

    # Confirm renaming operation
    is_input_invalid = True
    while is_input_invalid:
        confirm = input("Continue with file renaming? (y/n) ")
        if confirm == "n":
            print("Rename cancelled.")
            print("Exiting...")
            exit()
        if confirm == "y":
            is_input_invalid = False

    # Do renaming operation
    print("Processing rename...")
    for filename in final_pre_rename_files:
        try:
            os.rename(str(path_to_directory / filename), str(path_to_directory / files_oldtonew[filename]))
        except:
            print("An error occurred when trying to rename {}".format(filename))

    print("Rename done.")
    print("Exiting...")
    exit()

if __name__ == '__main__':
    main(sys.argv)
