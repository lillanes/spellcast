"""spellcast.dlna: DLNA related utilities (discovery and AV control)"""

import logging
import re
import socket

from http import client
from io import BytesIO
from urllib import parse, request

from requests import post

DISCOVER = "M-SEARCH * HTTP/1.1\r\nHOST: {0}:{1}\r\nMAN: \"ssdp:discover\"\r\nST: urn:schemas-upnp-org:service:AVTransport:1\r\nMX: 3\r\n\r\n\r\n"

SETURI = '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>$$$URI$$$</CurrentURI><CurrentURIMetaData></CurrentURIMetaData></u:SetAVTransportURI></s:Body></s:Envelope>'

PLAY = '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Play></s:Body></s:Envelope>'

EXPR_URI = re.compile(r"urn:upnp-org:serviceId:AVTransport.*?<controlURL>(.*?)</controlURL>", re.DOTALL)
EXPR_NAME = re.compile(r"<friendlyName>(.*?)</friendlyName>", re.DOTALL)


class SsdpFakeSocket(BytesIO):
    def makefile(self, *args, **kw): return self


def ssdp_discover(attempts):
    group = ("239.255.255.250", 1900)
    socket.setdefaulttimeout(0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    for _ in range(attempts):
        sock.sendto(DISCOVER.format(*group).encode('utf-8'), group)
    results = []
    while True:
        try:
            response = client.HTTPResponse(SsdpFakeSocket(sock.recv(1024)))
            response.begin()
            results.append(response.getheader("location"))
        except socket.timeout:
            break
    return results


def cast(tv, port):
    host = get_host_ip(tv["ip"])
    message = SETURI.replace("$$$URI$$$", f"http://{host}:{port}/media.mp4")
    send_message(tv["ip"], tv["port"], tv["url"], message, "SetAVTransportURI")
    send_message(tv["ip"], tv["port"], tv["url"], PLAY, "Play")


def discover(attempts=2):
    results = ssdp_discover(attempts)
    tvs = []
    for result in results:
        logging.debug(result)
        data = request.urlopen(result).read().decode()
        # logging.debug(data)
        control_uri = EXPR_URI.findall(data)
        name = EXPR_NAME.findall(data)
        logging.debug(control_uri)
        o = parse.urlparse(result)
        tv = {"ip": o.hostname, "port": o.port, "url": control_uri[0], "name": name[0]}
        logging.debug(tv)
        tvs.append(tv)
    return tvs


def get_host_ip(target_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((target_ip, 0))
        return s.getsockname()[0]


def send_message(ip, port, uri, message, action):
    headers = {"Content-Type": "text/xml; charset=utf-8",
               "SOAPAction": f"\"urn:schemas-upnp-org:service:AVTransport:1#{action}\"",
               }
    post(f"http://{ip}:{port}{uri}", headers=headers, data=message)
