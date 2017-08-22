import gevent
import gevent.event
import gevent.greenlet
import json

from gevent.socket import error as socket_error
from gevent.socket import timeout as socket_timeout
from gevent.server import StreamServer
from gevent import socket
from io import BlockingIOError
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.monitoring_integration.alert.handlers import AlertHandlerManager

class AlertReceiver(gevent.greenlet.Greenlet):
    def __init__(self):
        super(AlertReceiver, self).__init__()
        self.server = StreamServer(
            ("10.70.43.167", 10007),
            self.read_socket
        )
        self.alert_handler = AlertHandlerManager()

    def read_socket(self, sock, *args):
        try:
            data = sock.recv(2048)
            data = json.loads(data.split("\r\n\r\n")[-1])
            self.alert_handler.handle_alert(data["ruleId"])
        except (socket_error, socket_timeout) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "alert receiver socket error",
                        "exception": ex
                    }
                )
            )

    def _run(self):
        try:
            self.server.serve_forever()
        except (TypeError,
                BlockingIOError,
                socket_error,
                ValueError) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Unable to start alert receiving socket",
                        "exception": ex
                    }
                )
            )       

    def stop(self):
        pass   
