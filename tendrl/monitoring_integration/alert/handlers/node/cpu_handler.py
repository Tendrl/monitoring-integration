from etcd import EtcdKeyNotFound
from subprocess import CalledProcessError

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert.exceptions import InvalidAlertSeverity
from tendrl.monitoring_integration.alert.exceptions import NodeNotFound
from tendrl.monitoring_integration.alert.handlers import AlertHandler

from tendrl.monitoring_integration.alert import constants
from tendrl.monitoring_integration.alert import utils


class CpuHandler(AlertHandler):

    handles = 'cpu'
    representive_name = 'cpu_utilization'

    def __init__(self):
        AlertHandler.__init__(self)
        self.template = \
            "tendrl[.]name[.]{integration_id}[.]nodes[.]{host_name}[.]"

    def format_alert(self, alert_json):
        alert = self.parse_alert_metrics(alert_json)
        try:
            alert["alert_id"] = None
            alert["node_id"] = utils.find_node_id(
                alert['tags']['integration_id'],
                alert['tags']['fqdn']
            )
            alert["time_stamp"] = alert_json['NewStateDate']
            alert["resource"] = self.representive_name
            alert['alert_type'] = constants.ALERT_TYPE
            alert['significance'] = constants.SIGNIFICANCE_HIGH
            alert['pid'] = utils.find_grafana_pid()
            alert['source'] = constants.ALERT_SOURCE
            alert['tags']['fqdn'] = alert['tags']['fqdn']
            if alert_json['State'] == constants.GRAFANA_ALERT:
                if "critical" in alert_json['Name'].lower():
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['critical']
                else:
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['warning']
                alert['tags']['message'] = (
                    "Cpu utilization on node %s in %s"
                    " at %s %% and running out of cpu" % (
                        alert['tags']['fqdn'],
                        alert['tags']['integration_id'],
                        alert['current_value']))
            elif alert_json['State'] == constants.GRAFANA_CLEAR_ALERT:
                # Identifying clear alert from which panel critical/warning
                if "critical" in alert_json['Name'].lower():
                    alert['tags']['clear_alert'] = \
                        constants.TENDRL_SEVERITY_MAP['critical']
                elif "warning" in alert_json['Name'].lower():
                    alert['tags']['clear_alert'] = \
                        constants.TENDRL_SEVERITY_MAP['warning']
                alert['severity'] = constants.TENDRL_SEVERITY_MAP['info']
                alert['tags']['message'] = \
                    ("Cpu utilization on node %s in"
                        " %s back to normal" % (
                            alert['tags']['fqdn'],
                            alert['tags']['integration_id']))
            else:
                logger.log(
                    "error",
                    NS.publisher_id,
                    {
                        "message": "Unsupported alert %s "
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
                    "debug",
                    NS.publisher_id,
                    {
                        "message": "Error in converting grafana"
                        "alert into tendrl alert %s" % alert_json,
                        "exception": ex
                    }
                )
            )

    def parse_alert_metrics(self, alert_json):
        """{

         "EvalData": {
             "evalMatches": [{
                 "metric": "sumSeries(sumSeries(tendrl.clusters.ab3b125e-4769
                           -4071-a349-e82b380c11f4.nodes.{host_name}.
                           cpu.percent-system),sumSeries(tendrl.clusters.ab3b125e-4769-4071
                           -a349-e82b380c11f4.nodes.{host_name}.cpu.
                           percent-user))",
                 "tags": null,
                 "value": 31.97861830493573
              }]},
         "Settings": {
             "conditions": [{
                "evaluator": {
                   "params": [29],
                   "type": "gt"},
                query": {
                  "model": {
                    "target"    : "sumSeries(#A, #B).select metric",
                    "targetFull": "sumSeries(sumSeries(tendrl.clusters.
                                   ab3b125e-4769-4071-a349-e82b380c11f4.nodes.
                                   {host_name}.cpu.percent-system),
                                   sumSeries(tendrl.clusters.ab3b125e-4769-4071-a349-e82b
                                   380c11f4.nodes.{host_name}.cpu.
                                   percent-user)).select metric"
                   }
                }
             }]
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
        # identifying integration_id and node_id from target
        # Cpu target is an aggregation, So spliting and giving [0]
        # Because both have same cluster and node ids
        result = utils.parse_target(target, self.template)
        alert['tags']['integration_id'] = result["integration_id"]
        cluster_name = utils.find_cluster_short_name(
            result["integration_id"]
        )
        if cluster_name:
            alert['tags']['cluster_short_name'] = cluster_name
        else:
            alert['tags']['cluster_short_name'] = result["integration_id"]
        alert["tags"]["fqdn"] = result["host_name"].replace("_", ".")
        return alert
