import importlib
import inspect
import json
import os
import six

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert.exceptions import AlertNotFound
from tendrl.monitoring_integration.alert.exceptions import Unauthorized
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.grafana.exceptions import ConnectionFailedException
from tendrl.monitoring_integration.objects.alert_types import AlertTypes

class NoHandlerException(Exception):
    pass


class HandlerMount(type):

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'handlers'):
            cls.handlers = []
        else:
            cls.register_handler(cls)

    def register_handler(cls, handler):
        instance = handler()
        cls.handlers.append(instance)


@six.add_metaclass(HandlerMount)
class AlertHandler(object):
    handles = ''
    representive_name = ''

    def __init__(self):
        self.alert = None

    def handle(self, alert_json):
        alert = self.format_alert(alert_json)
        logger.log( 
            "notice",
            NS.publisher_id,
            {
                "message" : json.dumps(alert)
            }
        )


class AlertHandlerManager(object):
    def _load_handlers(self):
        path = os.path.dirname(os.path.abspath(__file__))
        pkg = 'tendrl.monitoring_integration.alert.handlers'
        handlers = utils.list_modules_in_package_path(path, pkg)
        for name, handler_fqdn in handlers:
            mod = importlib.import_module(handler_fqdn)
            clsmembers = inspect.getmembers(mod, inspect.isclass)
            for name, cls in clsmembers:
                if issubclass(cls, AlertHandler) and cls.handles:
                    self.alert_handlers.append(cls.handles)

    def __init__(self):
        self.alert_handlers = []
        self._load_handlers()
        self._save_alert_types()

    def _save_alert_types(self):
        alert_types = {}
        for handler in AlertHandler.handlers:
            alert_types[handler.representive_name] = "true"
        AlertTypes(types=alert_types).save()

        
    def handle_alert(self, alert_id):
        try:
            alert_json = utils.get_alert_info(alert_id)
            handled_alert = False
            for handler in AlertHandler.handlers:
                if handler.handles in alert_json['Name'].lower():
                    handler.handle(alert_json)
                    handled_alert = True
            if not handled_alert:
                logger.log(
                    "error",
                    NS.publisher_id,
                    {
                        "message": 'No alert handler defined for '
                        '%s and hence cannot handle alert %s' % (
                            alert_json['Name'],
                            alert_json,
                        )
                    }
                )
        except(AlertNotFound, Unauthorized, ConnectionFailedException) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={
                        "message": "Unable to fetch complete alert info"
                        " for alert_id: %s" % alert_id,
                        "exception": ex
                    }
                )
            )
