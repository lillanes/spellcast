"""spellcast.server: HTTP server for a single file to be streamed via DLNA"""

import os
import tempfile
import threading

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File


class DLNAFile(File):
    def render_GET(self, request):
        request.setHeader("ContentFeatures.DLNA.ORG", "DLNA.ORG_PN=MPEG4_P2_SP_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000")
        request.setHeader("TransferMode.DLNA.ORG", "Streaming")
        return super().render_GET(request)

    def render_HEAD(self, request):
        return self.render_GET(request)


class DLNAFileServer():
    def __init__(self, verbose=False):
        self.thread = None
        if verbose:
            log.PythonLoggingObserver().start()

    def serve_media(self, media, ready, port):
        with tempfile.TemporaryDirectory() as path:
            os.chdir(path)
            os.symlink(media, "media.mp4")
            open("index.html", "w").close()
            port.append(reactor.listenTCP(0, Site(DLNAFile(path))).getHost().port)
            ready.set()
            reactor.run(installSignalHandlers=False)

    def start(self, media):
        port = []
        ready = threading.Event()
        self.thread = threading.Thread(target=self.serve_media, args=(media, ready, port,))
        self.thread.start()

        ready.wait()
        return port[0]

    def wait(self):
        try:
            print("Send interrupt to stop (Ctrl-C).")
            self.thread.join()
        except KeyboardInterrupt:
            print("Cleaning up...")
            reactor.stop()
