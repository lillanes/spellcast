#!/usr/bin/env python3

# This code is heavily based on https://github.com/probonopd/video2smarttv

import argparse
import logging
import os
import sys
import threading

import dlna
import server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="Cast a video file to a UPnP Media Renderer (e.g., a Smart TV)",
            add_help=True)
    parser.add_argument("-v", "--verbose", help="print debug information", action='store_true')
    parser.add_argument('video', nargs=1, default=None,
                        help='video file to be sent to renderer')

    args = parser.parse_args()
    args.video = os.path.abspath(args.video[0])
    if args.verbose:
        server.start_logging()
        logging.basicConfig(level=logging.DEBUG)

    tvs = dlna.discover()

    if len(tvs) > 1:
        logging.warning("Multiple TVs found. Choice not implemented. Will use first one found.")

    if tvs:
        for tv in tvs:
            print("TV:", tv["name"])
        tv = tvs[0]
    else:
        print("No TVs found.")
        sys.exit(1)

    host = [None, None]

    server_ready = threading.Event()
    server_thread = threading.Thread(target=server.serve_media, args=(args.video, host, server_ready,))
    server_thread.start()

    server_ready.wait()
    print(f"Casting to \"{tv['name']}\"...")
    dlna.cast(host, tv)

    print("Done. Send interrupt (Ctrl-C) to exit.")
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("Cleaning up...")
        server.stop()
