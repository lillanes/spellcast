#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from dlna import cast, discover
from server import DLNAFileServer


def get_cli_arguments():
    parser = argparse.ArgumentParser(
            description="Cast a video file to a UPnP Media Renderer (e.g., a Smart TV)",
            add_help=True)
    parser.add_argument("-v", "--verbose", help="print debug information", action='store_true')
    parser.add_argument('video', nargs=1, default=None,
                        help='video file to be sent to renderer')

    args = parser.parse_args()
    args.video = os.path.abspath(args.video[0])
    return args


def get_tv():
    tvs = discover()

    if len(tvs) > 1:
        logging.warning("Multiple TVs found. Choice not implemented. Will use first one found.")

    if tvs:
        for tv in tvs:
            print("TV:", tv["name"])
        return tvs[0]
    else:
        print("No TVs found.")
        sys.exit(1)


if __name__ == '__main__':
    args = get_cli_arguments()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    tv = get_tv()

    server = DLNAFileServer(args.verbose)
    port = server.start(args.video)

    print(f"Casting to \"{tv['name']}\"...")
    cast(tv, port)

    server.wait()
