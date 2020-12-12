import os
import tempfile

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File


#
# Function to discover services on the network using SSDP
# Inspired by https://gist.github.com/dankrause/6000248
#

class DLNAFile(File):
    def render_GET(self, request):
        request.setHeader("ContentFeatures.DLNA.ORG", "DLNA.ORG_PN=MPEG4_P2_SP_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000")
        request.setHeader("TransferMode.DLNA.ORG", "Streaming")
        return super().render_GET(request)

    def render_HEAD(self, request):
        return self.render_GET(request)


def serve_media(media, host, ready):
    global PORT
    with tempfile.TemporaryDirectory() as path:
        os.chdir(path)
        os.symlink(media, "media.mp4")
        open("index.html", "w").close()
        host[1] = reactor.listenTCP(0, Site(DLNAFile(path))).getHost().port
        ready.set()
        reactor.run(installSignalHandlers=False)


def start_logging():
    log.PythonLoggingObserver().start()


def stop():
    reactor.stop()
