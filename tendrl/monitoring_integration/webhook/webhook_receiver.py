import cherrypy
from flask import Flask
from flask import request
from paste.translogger import TransLogger
import socket
import threading

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert.handlers import AlertHandlerManager

PORT = 8789
app = Flask(__name__)


class WebhookReceiver(threading.Thread):
    def __init__(self):
        super(WebhookReceiver, self).__init__()
        self.daemon = True

    @app.route('/grafana_callback', methods=["POST"])
    def _application():
        try:
            alert_handler = AlertHandlerManager()
            data = request.json
            if "ruleId" in data:
                alert_handler.handle_alert(
                    data["ruleId"]
                )
            else:
                logger.log(
                    "debug",
                    NS.publisher_id,
                    {
                        "message": "Unable to find ruleId %s" % data
                    }
                )
        except (IOError, AssertionError, KeyError) as ex:
            Event(
                ExceptionMessage(
                    priority="debug",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Unable to handle grafana alert",
                        "exception": ex
                    }
                )
            )
        return "OK"

    def run(self):
        app_logged = TransLogger(app)
        cherrypy.tree.graft(app_logged, '/')
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'log.screen': True,
            'server.socket_port': PORT,
            'server.socket_host': socket.gethostbyname(
                socket.gethostname()),
            'log.access_file': '',
            'log.error_file': ''
        })
        # Start the CherryPy WSGI web server
        cherrypy.engine.start()
        cherrypy.engine.block()

    def stop(self):
        pass
