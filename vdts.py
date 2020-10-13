#!/home/stephen/miniconda3/bin/python
###############################################################################
# Author: Stephen Zhao
# App: vdts (Verify Directory as Time-Series)
# Version: v0.1.0
# Last modified: 2020-10-12
# Description: Check for missing and extra files by datetime in the filename

import argparse
from datetime_matcher import DatetimeMatcher
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from pathlib import Path
import sys
from typing import Any, List, NamedTuple

IS_DEBUG = True

def debug(*args):
    if IS_DEBUG:
        print('[DEBUG]', *args)

TIME_INTERVALS = [
    'y', 'q', 'm', 'w', 'd'
]

class FuzzyTimeDelta(NamedTuple):
    delta: relativedelta
    margin: relativedelta

def get_fuzzy_time_delta_from_time_interval(time_interval: str) -> FuzzyTimeDelta:
    if time_interval not in TIME_INTERVALS:
        raise ValueError('time_interval must be in TIME_INTERVALS')
    elif time_interval == 'y':
        return FuzzyTimeDelta(relativedelta(years=1), relativedelta(months=1))
    elif time_interval == 'q':
        return FuzzyTimeDelta(relativedelta(months=3), relativedelta(months=1))
    elif time_interval == 'm':
        return FuzzyTimeDelta(relativedelta(months=1), relativedelta(weeks=1))
    elif time_interval == 'w':
        return FuzzyTimeDelta(relativedelta(weeks=1), relativedelta(days=3))
    elif time_interval == 'd':
        return FuzzyTimeDelta(relativedelta(days=1), relativedelta(hours=10))
    else:
        raise NotImplementedError('time_interval is in TIME_INTERVALS, but not implemented')

def get_string_from_time_interval(time_interval: str, t: datetime) -> str:
    if time_interval not in TIME_INTERVALS:
        raise ValueError('time_interval must be in TIME_INTERVALS')
    elif time_interval == 'y':
        return t.strftime('%Y')
    elif time_interval == 'q':
        return f"{t.strftime('%Y')}-Q{t.month // 3 + 1}"
    elif time_interval == 'm':
        return t.strftime('%Y-%m (%B %Y)')
    elif time_interval == 'w':
        return t.strftime('Week of %Y-%m-%d (week #%U)')
    elif time_interval == 'd':
        return t.strftime('%Y-%m-%d')
    else:
        raise NotImplementedError('time_interval is in TIME_INTERVALS, but not implemented')

def create_argparser() -> argparse.ArgumentParser:
    argparser = argparse.ArgumentParser(
        description="Check for missing files by datetime in a time-series.")
    argparser.add_argument('-i', '--interval', nargs='?', choices=TIME_INTERVALS, default='m', help='The interval at which points should occur in the time series. Defaults to monthly (m).')
    argparser.add_argument('-n', '--end-now', action='store_true', help='Use the current time as the endpoint of the time series.')
    argparser.add_argument('in_dir', help='The input directory to verify as a time series.')
    argparser.add_argument('file_pattern', help='A dfregex which determines relevent files and extracts the necessary datetimes from the file names.')
    return argparser

def main(argv):
    # Parse arguments
    argparser = create_argparser()
    args = argparser.parse_args(argv)

    # Get path to directory
    in_dir_path = Path(args.in_dir)

    # Handle directory path errors
    if in_dir_path.is_file():
        print("Input directory cannot be a file.")
        argparser.print_usage()
        exit(2)
    if not in_dir_path.is_dir():
        print("Input directory is not a valid directory.")
        argparser.print_usage()
        exit(3)

    # Get the time delta
    interval = get_fuzzy_time_delta_from_time_interval(args.interval)

    # Get list of files in directory
    files = list(file for file in os.listdir(str(in_dir_path)) if (in_dir_path / file).is_file())

    # Extract the datetimes
    dtmatcher = DatetimeMatcher()
    timepoint_files = list((dtmatcher.extract_datetime(args.file_pattern, file), file) for file in files)

    # Filter out Nones as those without a datetime cannot be a part of the time series
    timepoint_to_file = dict((timepoint, file) for timepoint, file in timepoint_files if timepoint is not None)
    sorted_timepoints = sorted(timepoint_to_file.keys())

    # Check if there are any files left
    if len(sorted_timepoints) == 0:
        print("No files from which a time series could be inferred exist in the provided directory.")
        exit(0)

    missing_timepoints = []
    extra_timepoints = []
    # Begin the time series at the time point of the oldest file
    truth_ts_curr_point = sorted_timepoints[0]
    # Go through and mark any missing or extra files by interpolation
    file_ts = iter(sorted_timepoints)
    file_ts_curr_point = next(file_ts)
    while True:
        try:
            if truth_ts_curr_point - interval.margin <= file_ts_curr_point <= truth_ts_curr_point + interval.margin:
                truth_ts_curr_point = file_ts_curr_point + interval.delta
                file_ts_curr_point = next(file_ts)
            elif truth_ts_curr_point + interval.margin < file_ts_curr_point:
                missing_timepoints.append(truth_ts_curr_point)
                truth_ts_curr_point += interval.delta
            elif file_ts_curr_point < truth_ts_curr_point - interval.margin:
                extra_timepoints.append(file_ts_curr_point)
                file_ts_curr_point = next(file_ts)
            else:
                raise ValueError('Invalid truth_ts_curr_point or file_ts_curr_point')
        except StopIteration:
            break
    # If we are to check until now, then continue extrapolating
    truth_ts_curr_point = sorted_timepoints[-1] + interval.delta
    truth_ts_now_point = datetime.now()
    if args.end_now and truth_ts_curr_point < truth_ts_now_point:
        while truth_ts_curr_point + interval.margin < truth_ts_now_point:
            missing_timepoints.append(truth_ts_curr_point)
            truth_ts_curr_point += interval.delta
    
    # Display results to user
    all_timepoints = sorted(sorted_timepoints + missing_timepoints)
    for timepoint in all_timepoints:
        filename = timepoint_to_file.get(timepoint)
        if filename is None:
            print(f">>> Missing file for timepoint {get_string_from_time_interval(args.interval, timepoint)} <<< ❌")
        elif timepoint in extra_timepoints:
            print(f">>> Extra file for timepoint {timepoint.isoformat()} <<< ❗")
        else:
            print(f"{filename} <<< ✅")

if __name__ == '__main__':
    main(sys.argv[1:])
