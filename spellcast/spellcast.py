"""spellcast.spellcast: main entry point for sending video to DLNA media renderer"""

import argparse
import logging
import os
import sys

from .dlna import cast, discover
from .server import DLNAFileServer


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
    while True:
        print("Finding media renderers...")
        tvs = discover()

        if not tvs:
            print("No renderers found.")

        while True:
            print()
            i = 0
            for i, tv in enumerate(tvs):
                print(f"{i}: use \"{tv['name']}\"")

            print(f"{i+1}: try again")
            print(f"{i+2}: exit")

            try:
                option = int(input("Select an option: "))
                if option > i + 2 or option < 0:
                    continue
                break
            except ValueError:
                pass

        if option == i + 2:
            sys.exit(0)
        if option == i + 1:
            continue

        return tvs[option]


def main():
    args = get_cli_arguments()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    tv = get_tv()

    server = DLNAFileServer(args.verbose)
    port = server.start(args.video)

    print(f"Casting to \"{tv['name']}\"...")
    cast(tv, port)

    server.wait()
