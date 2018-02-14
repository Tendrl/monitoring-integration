import json
import threading

from werkzeug.serving import run_simple
from werkzeug.wrappers import Response

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert.handlers import AlertHandlerManager

PORT = 8789


class WebhookReceiver(threading.Thread):
    def __init__(self):
        super(WebhookReceiver, self).__init__()
        self.daemon = True
        self.alert_handler = AlertHandlerManager()

    def _application(self, env, start_response):
        try:
            if env['PATH_INFO'] != '/grafana_callback':
                response = Response('Alert not found')
                response.headers['content-length'] = len(response.data)
                response.status_code = 404
            else:
                data = env['wsgi.input'].read(
                    int(env['CONTENT_LENGTH'])
                )
                data = json.loads(data)
                if "ruleId" in data:
                    self.alert_handler.handle_alert(
                        data["ruleId"]
                    )
                    response = Response('Alert received successfully')
                    response.headers['content-length'] = len(response.data)
                    response.status_code = 200
                else:
                    logger.log(
                        "error",
                        NS.publisher_id,
                        {
                            "message": "Unable to find ruleId %s" % data
                        }
                    )
        except (IOError, AssertionError, KeyError) as ex:
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
            response = Response('Error in reading alert from socket')
            response.headers['content-length'] = len(response.data)
            response.status_code = 500
        return response(env, start_response)

    def run(self):
        try:
            run_simple(
                NS.node_context.fqdn,
                PORT,
                self._application, threaded=True
            )
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
