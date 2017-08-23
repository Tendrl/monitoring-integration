from etcd import EtcdKeyNotFound
from subprocess import CalledProcessError
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.monitoring_integration.alert import constants
from tendrl.monitoring_integration.alert.handlers import AlertHandler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.alert.exceptions import InvalidAlertSeverity
from tendrl.monitoring_integration.alert.exceptions import NodeNotFound


class MemoryHandler(AlertHandler):

    handles = 'memory'
    representive_name = 'memory_alert'

    def __init__(self):
        AlertHandler.__init__(self)

    def format_alert(self, alert_json):
        alert  = self.parse_alert_metrics(alert_json)
        try:
            alert["alert_id"] = None
            alert["node_id"] = utils.find_node_id(
                alert['tags']['integration_id'],
                alert['tags']['fqdn']
            )
            alert["time_stamp"] = alert_json['NewStateDate']
            alert["resource"] = self.representive_name
            alert['alert_type'] = constants.ALERT_TYPE 
            alert['severity'] = constants.TENDRL_GRAFANA_SEVERITY_MAP[
                alert_json['State']]
            alert['significance'] = constants.SIGNIFICANCE_HIGH
            alert['pid'] = utils.find_grafana_pid()
            alert['source'] = constants.ALERT_SOURCE
            alert['tags']['fqdn'] = alert['tags']['fqdn']
            alert['tags']['alert_catagory'] = constants.NODE
            if alert['severity'] == "WARNING":
                alert['tags']['message'] = ("Memory utilization of node %s is" \
                " %s which is above the %s threshold (%s)." % (
                    alert['tags']['fqdn'],
                    alert['current_value'],
                    alert['severity'],
                    alert['tags']['warning_max']
                ))
            elif alert['severity'] == "INFO":
                alert['tags']['message'] = ("Memory utilization of node %s is"\
                " back to normal" % (
                    alert['tags']['fqdn']
                ))
            else:
                logger.log(
                    "error",
                    NS.publisher_id,
                    {
                        "message": "Alert %s have unsupported alert"
                        "severity" % alert_json
                    }
                )
                raise InvalidAlertSeverity
            return alert
        except (KeyError,
                CalledProcessError,
                EtcdKeyNotFound,
                NodeNotFound,
                InvalidAlertSeverity) as ex:
            Event(
                ExceptionMessage(
                    "error",
                    NS.publisher_id, 
                    {
                        "message": "Error in converting grafana"
                        "alert into tendrl alert %s" % alert_json,
                        "exception": ex
                    }
                )
            )
    
    def parse_alert_metrics(self, alert_json):
        """
        {
          "EvalData": {
            "evalMatches": [{
              "metric": "tendrl.clusters.ab3b125e-4769-4071-a349-
                        e82b380c11f4.nodes.dhcp43-213_lab_eng_blr_
                        redhat_com.memory.memory-buffered",
              "tags": null,
              "value": 4096
            }]
          },
          "Settings": {
            "conditions": [{
              "evaluator": {
                "params": [3664],
                "type": "gt"
              },
            "query": {
              "model": {
                "target": "tendrl.clusters.ab3b125e-4769-4071-
                          a349-e82b380c11f4.nodes.dhcp43-213_lab_eng_
                          blr_redhat_com.memory.memory-buffered"
              },
            }
          }
        }
        """
        alert = {}
        alert['tags'] = {}
        alert['current_value'] = utils.find_current_value(
            alert_json['EvalData'])
        target = utils.find_alert_target(
            alert_json['Settings']['conditions'])
        alert['tags']['warning_max'] = utils.find_warning_max(
            alert_json['Settings']['conditions'][0]['evaluator']['params'])
        # identifying cluster_id and node_id from any one
        # alert metric (all have same)
        metric = target.split(",")[0].split(".")
        for i in range(0, len(metric)):
            if  metric[i] == "clusters":
                alert['tags']['integration_id'] = metric[i + 1]
            elif metric[i] == "nodes":
                alert["tags"]["fqdn"] = metric[i + 1].replace("_", ".")
        return alert
