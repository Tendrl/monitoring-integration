import gevent
import gevent.greenlet
import json

from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.monitoring_integration.alert.handlers import AlertHandlerManager

HOST = "127.0.0.1"
PORT = 8789


class WebhookReceiver(gevent.greenlet.Greenlet):
    def __init__(self):
        super(WebhookReceiver, self).__init__()
        self.server = WSGIServer(
            (HOST, PORT),
            self._application
        )
        self.alert_handler = AlertHandlerManager()
        
    def _application(self, env, start_response):
        try:
            if env['PATH_INFO'] != '/grafana_callback':
                start_response(
                    '404 Not Found',
                    [('Content-Type', 'text/html')]
                )
                response = [b'<h1>Alert Not Found</h1>']
            else:
                data = env['wsgi.input'].read()
                data = json.loads(data)
                self.alert_handler.handle_alert(
                    data["ruleId"]
                )
                start_response(
                    '200 OK',
                    [('Content-Type', 'text/html')]
                )
                response = [b'<h1>Alert Received</h1>']
        except (IOError, AssertionError) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Unable to read alert from socket",
                        "exception": ex
                    }
                )
            )
            response = [b'<h1>Error in reading alert from socket</h1>']

        return response

    def _run(self):
        try:
            self.server.serve_forever()
        except (TypeError,
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
