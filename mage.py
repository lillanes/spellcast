#!/usr/bin/env python3

#
# Send mp4 streaming media URIs to Samsung Smart TV for immediate playback
#

import argparse
import html
import logging
import os
import re
import requests
import socket
import subprocess
import sys
import tempfile
import threading

from http import client
from io import BytesIO
from urllib import parse, request

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

#
# Function to discover services on the network using SSDP
# Inspired by https://gist.github.com/dankrause/6000248
#


class SsdpFakeSocket(BytesIO):
    def makefile(self, *args, **kw): return self


def ssdp_discover(service):
    group = ("239.255.255.250", 1900)
    message = "\r\n".join(['M-SEARCH * HTTP/1.1', 'HOST: {0}:{1}', 'MAN: "ssdp:discover"', 'ST: {st}', 'MX: 3', '', ''])
    socket.setdefaulttimeout(0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(message.format(*group, st=service).encode('utf-8'), group)
    results = []
    while True:
        try:
            response = client.HTTPResponse(SsdpFakeSocket(sock.recv(1024)))
            response.begin()
            results.append(response.getheader("location"))
        except socket.timeout:
            break
    return results


AVTransportTemplate = f'<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>$$$URI$$$</CurrentURI><CurrentURIMetaData></CurrentURIMetaData></u:SetAVTransportURI></s:Body></s:Envelope>'

PlayMessage = '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Play></s:Body></s:Envelope>'

HOST = None
PORT = None


def get_host_ip(target_ip):
    global HOST
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((target_ip, 0))
        HOST = s.getsockname()[0]


def send_message(ip, port, uri, message, action):
    headers = {"Content-Type": "text/xml; charset=utf-8",
               "SOAPAction": f"\"urn:schemas-upnp-org:service:AVTransport:1#{action}\"",
               }
    response = requests.post(f"http://{ip}:{port}{uri}", headers=headers,
                             data=message)


def prepare_media(media):
    print(f"Preparing media ({media})...")
    os.symlink(media, "media.mp4")
    # subprocess.run(["cp", media, "media.mp4"])
    # subprocess.run(["ffmpeg", "-i", media, "-codec", "copy", "media.mp4"])


class DLNAFile(File):
    def render_GET(self, request):
        request.setHeader("ContentFeatures.DLNA.ORG", "DLNA.ORG_PN=MPEG4_P2_SP_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000")
        request.setHeader("TransferMode.DLNA.ORG", "Streaming")
        return super().render_GET(request)

    def render_HEAD(self, request):
        return self.render_GET(request)


def serve_media(media, lock):
    global PORT
    with tempfile.TemporaryDirectory() as path:
        os.chdir(path)
        prepare_media(media)
        open("index.html", "w").close()
        PORT = reactor.listenTCP(0, Site(DLNAFile(path))).getHost().port
        print(f"Serving on {HOST}:{PORT}...")
        lock.release()
        reactor.run(installSignalHandlers=False)


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
        log.PythonLoggingObserver().start()
        logging.basicConfig(level=logging.DEBUG)

    tvs = []
    results = ssdp_discover("urn:schemas-upnp-org:service:AVTransport:1")
    expr_uri = re.compile(r"urn:upnp-org:serviceId:AVTransport.*?<controlURL>(.*?)</controlURL>", re.DOTALL)
    expr_name = re.compile(r"<friendlyName>(.*?)</friendlyName>", re.DOTALL)
    for result in results:
        logging.debug(result)
        data = request.urlopen(result).read().decode()
        # logging.debug(data)
        control_uri = expr_uri.findall(data)
        name = expr_name.findall(data)
        logging.debug(control_uri)
        o = parse.urlparse(result)
        tv = {"ip": o.hostname, "port": o.port, "url": control_uri[0], "name": name[0]}
        logging.debug(tv)
        tvs.append(tv)

    if len(tvs) > 1:
        logging.warning("Multiple TVs found. Choice not implemented. Will use first one found.")

    if tvs:
        for tv in tvs:
            print("TV:", tv["name"])
        tv = tvs[0]
    else:
        print("No TVs found.")
        sys.exit(1)

    get_host_ip(tv["ip"])

    lock = threading.Lock()
    lock.acquire()
    threading.Thread(target=serve_media, args=(args.video, lock,)).start()

    lock.acquire()
    print(f"Casting to \"{tv['name']}\"...")
    message = AVTransportTemplate.replace("$$$URI$$$",
                                          f"http://{HOST}:{PORT}/media.mp4")
    send_message(tv["ip"], tv["port"], tv["url"], message, "SetAVTransportURI")
    send_message(tv["ip"], tv["port"], tv["url"], PlayMessage, "Play")
