#!/usr/bin/env python3

import sys
req_version = (3, 0)
cur_version = sys.version_info

if cur_version < req_version:
    print("Error! you need to use this script with Python 3+")
    exit(0)

import mailbox
import argparse
from pathlib import Path
from collections import defaultdict
import re

DEFAULT_THRESHOLD = 50

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mbox_path", help="the path of the mbox file")
    parser.add_argument("--threshold", '-t', help="number of mails/bytes to use as the threshold", default=DEFAULT_THRESHOLD, type=int)
    parser.add_argument("--from", '-f', help="use the entire FROM field for grouping", dest="strip_emails", default=True, action="store_false")
    parser.add_argument("--count", '-c',  help="only count the number of emails rather than the size", dest="report_size", default=True, action="store_false")
    return parser.parse_args()

def open_mbox_file():
    my_file = Path(args.mbox_path)
    if not my_file.is_file():
        print("path '%s' is not a file" % args.mbox_path)
        exit(0)
    return mailbox.mbox(args.mbox_path)

def get_frequencies(mbox, args):
    frequencies = defaultdict(lambda: 0)
    for message in mbox:
        if args.strip_emails:
            matches = re.findall(r'[\w.+-]+@[\w.+-]+', message['from'])
            key = matches[0] if len(matches) > 0 else "no email found"
        else:
            key = message['from']

        if args.report_size:
            frequencies[key] += int(message['Content-Length'])
        else:
            frequencies[key] += 1

    return frequencies

def filter_frequencies(frequencies, threshold):
    return {
        key: count for key, count in frequencies.items()
        if count > threshold
    }

def sort_frequencies(frequencies):
    # this method will return a list of 2-Tuples
    return sorted(
        frequencies_filtered.items(),
        key=lambda kv: -kv[1]
    )

if __name__ == '__main__':
    args = parse_args()
    mbox = open_mbox_file()
    frequencies = get_frequencies(mbox, args)
    frequencies_filtered = filter_frequencies(frequencies, args.threshold)
    if len(frequencies_filtered) == 0:
        print("no matches ! no single sender sent you over %s mails" % args.threshold)
        exit(1)
    frequencies_sorted = sort_frequencies(frequencies_filtered)
    if args.report_size:
        for line in frequencies_sorted:
            print("%9s: '%s'" % (sizeof_fmt(line[1]), line[0]))
    else:
        for line in frequencies_sorted:
            print("%s mails from : '%s'" % (line[1], line[0]))

