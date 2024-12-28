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

import logging
from tqdm import tqdm
import tracking_mailbox
from datetime import datetime
import json
import traceback
import email

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
    parser.add_argument("--verbose", '-v', help="increase output verbosity", action="store_true")
    return parser.parse_args()

def setup_logging(verbose):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

def write_error_to_file(error_message, message_data):
    error_file = 'error_log.txt'
    with open(error_file, 'a') as f:
        f.write(f"Error occurred at: {datetime.now()}\n")
        f.write(f"Error message: {error_message}\n")
        f.write("Message data:\n")
        try:
            f.write(json.dumps(dict(message_data), indent=2))
        except Exception as json_error:
            f.write(f"Unable to serialize message data using json: {str(json_error)}\n")
            f.write("Falling back to pprint:\n")
            try:
                f.write(pprint.pformat(dict(message_data), indent=2))
            except Exception as pprint_error:
                f.write(f"Unable to serialize message data using pprint: {str(pprint_error)}\n")
                f.write("Falling back to str representation:\n")
                f.write(str(message_data))

        f.write("\nStack Trace:\n")
        f.write(traceback.format_exc())
        f.write("\n" + "-" * 50 + "\n\n")

def open_mbox_file():
    my_file = Path(args.mbox_path)
    if not my_file.is_file():
        logging.error("path '%s' is not a file", args.mbox_path)
        exit(0)

    return tracking_mailbox.TrackingMbox(args.mbox_path, print_progress=True, max_messages=1000)


def get_message_size(message):
    """
    Calculate the size of a message.
    First checks for Content-Length header, then calculates from content if not present.
    """

    # Content-Length' header is not a required header
    if 'Content-Length' in message:
        return int(message['Content-Length'])
    
    # If Content-Length is not present, calculate from content
    if message.is_multipart():
        return sum(len(part.as_bytes()) for part in message.walk())
    else:
        return len(message.get_payload(decode=True) or b'')



def get_frequencies(mbox, args):
    frequencies = defaultdict(lambda: 0)
    logging.info("Processing %d messages", len(mbox))

    for message in tqdm(mbox, desc="Processing messages", unit="percent"):
        try:
            if args.strip_emails:
                from_header = message['from']
                if not isinstance(from_header, email.header.Header):
                    # Use From if it's not a Header type
                    key_source = str(from_header)
                elif message['Return-Path']:
                    # Use Return-Path if From is a Header and Return-Path is available
                    key_source = str(message['Return-Path'])
                else:
                    # Fall back to string conversion of From Header
                    key_source = str(from_header)
                matches = re.findall(r'[\w.+-]+@[\w.+-]+', key_source)
                key = matches[0] if len(matches) > 0 else "no email found"
            else:
                # For non-stripped version, use the same logic but don't extract email
                from_header = message['from']
                if not isinstance(from_header, email.header.Header):
                    key = str(from_header)
                elif message['Return-Path']:
                    key = str(message['Return-Path'])
                else:
                    key = str(from_header)

            if args.report_size:
                frequencies[key] += get_message_size(message)
            else:
                frequencies[key] += 1
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            logging.error(error_message)
            write_error_to_file(error_message, message)
            if args.verbose:
                logging.debug(traceback.format_exc())

    logging.debug("Finished processing messages")
    return frequencies

def filter_frequencies(frequencies, threshold):
    logging.info("Filtering frequencies with threshold %d", threshold)
    filtered = {
        key: count for key, count in frequencies.items()
        if count > threshold
    }
    logging.debug("Filtered %d senders", len(filtered))
    return filtered


def sort_frequencies(frequencies):
    # this method will return a list of 2-Tuples
    return sorted(
        frequencies_filtered.items(),
        key=lambda kv: -kv[1]
    )

if __name__ == '__main__':
    args = parse_args()
    setup_logging(args.verbose)

    logging.info("Starting mbox analysis")
    mbox = open_mbox_file()
    frequencies = get_frequencies(mbox, args)
    frequencies_filtered = filter_frequencies(frequencies, args.threshold)
    if len(frequencies_filtered) == 0:
        logging.warning("no matches ! no single sender sent you over %s mails", args.threshold)
        exit(1)
    frequencies_sorted = sort_frequencies(frequencies_filtered)
    if args.report_size:
        for line in frequencies_sorted:
            print("%9s: '%s'" % (sizeof_fmt(line[1]), line[0]))
    else:
        for line in frequencies_sorted:
            print("%s mails from : '%s'" % (line[1], line[0]))

    logging.info("Analysis complete")

