import gevent
import gevent.event
import gevent.greenlet
import json

from gevent.pywsgi import WSGIServer
from gevent.socket import error as socket_error
from gevent.socket import timeout as socket_timeout
from gevent.server import StreamServer
from io import BlockingIOError
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.monitoring_integration.alert.handlers import AlertHandlerManager


class WebhookReceiver(gevent.greenlet.Greenlet):
    def __init__(self):
        super(WebhookReceiver, self).__init__()
        self.server = WSGIServer(
            ('127.0.0.1', 8789),
            self.application
        )
        self.alert_handler = AlertHandlerManager()
        
    def application(self, env, start_response):
        try:
            if env['PATH_INFO'] == '/grafana_callback':
                start_response(
                    '200 OK',
                    [('Content-Type', 'text/html')]
                )
                data = env['wsgi.input'].read()
                data = json.loads(data)
                self.alert_handler.handle_alert(data["ruleId"])
                return [b"<b>Recieved</b>"]
        except (socket_error, socket_timeout) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "webhook receiver socket error",
                        "exception": ex
                    }
                )
            )
        start_response(
            '404 Not Found',
            [('Content-Type', 'text/html')]
        )
        return [b'<h1>Not Found</h1>']

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
                        "message": "Unable to start wehook receiver",
                        "exception": ex
                    }
                )
            )            

    def stop(self):
        pass   
