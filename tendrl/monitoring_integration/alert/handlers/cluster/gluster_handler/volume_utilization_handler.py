from etcd import EtcdKeyNotFound
from subprocess import CalledProcessError

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils import log_utils as logger
from tendrl.commons.utils.time_utils import now as tendrl_now
from tendrl.monitoring_integration.alert.exceptions import InvalidAlertSeverity
from tendrl.monitoring_integration.alert.exceptions import NodeNotFound
from tendrl.monitoring_integration.alert.handlers import AlertHandler

from tendrl.monitoring_integration.alert import constants
from tendrl.monitoring_integration.alert import utils


class VolumeHandler(AlertHandler):

    handles = 'volume'
    representive_name = 'volume_utilization'

    def __init__(self):
        AlertHandler.__init__(self)
        self.template = "tendrl[.]clusters[.]{integration_id}[.]volumes[.]"\
            "{volume_name}[.]"

    def format_alert(self, alert_json):
        alert = self.parse_alert_metrics(alert_json)
        try:
            alert["alert_id"] = None
            alert["node_id"] = None
            alert["time_stamp"] = tendrl_now().isoformat()
            alert["resource"] = self.representive_name
            alert['alert_type'] = constants.ALERT_TYPE
            alert['significance'] = constants.SIGNIFICANCE_HIGH
            alert['pid'] = utils.find_grafana_pid()
            alert['source'] = constants.ALERT_SOURCE
            alert['tags']['cluster_name'] = utils.find_cluster_name(
                alert['tags']['integration_id'])
            if alert_json['State'] == constants.GRAFANA_ALERT:
                if "critical" in alert_json['Name'].lower():
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['critical']
                else:
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['warning']
                alert['tags']['message'] = (
                    "Volume utilization on %s in "
                    "%s at %s %% and nearing full capacity" % (
                        alert['tags']['volume_name'],
                        alert['tags']['cluster_short_name'],
                        alert['current_value']
                    )
                )
            elif alert_json['State'] == constants.GRAFANA_CLEAR_ALERT:
                # Identifying clear alert from which panel critical/warning
                if "critical" in alert_json['Name'].lower():
                    alert['tags']['clear_alert'] = \
                        constants.TENDRL_SEVERITY_MAP['critical']
                elif "warning" in alert_json['Name'].lower():
                    alert['tags']['clear_alert'] = \
                        constants.TENDRL_SEVERITY_MAP['warning']
                alert['severity'] = constants.TENDRL_SEVERITY_MAP['info']
                alert['tags']['message'] = (
                    "Volume utilization on %s in "
                    "%s back to normal" % (
                        alert['tags']['volume_name'],
                        alert['tags']['cluster_short_name']
                    )
                )
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

          EvalData: {
            evalMatches: - [{
              metric: "tendrl.clusters.ab3b125e-
                      4769-4071-a349-e82b380c11f4.volumes.vol1.
                      nodes.*.bricks.*.utilization.percent-percent_bytes",
              tags: null,
              value: 13407092736
            }]
          },
          Settings: {
            conditions: - [{
              evaluator: - {
                params: - [12138888889],
                type: "gt"
              },
              query: - {
                model: - {
                  target: "tendrl.clusters.ab3b125e-
                          4769-4071-a349-e82b380c11f4.volumes.vol1.
                          nodes.*.bricks.*.utilization.percent-percent_bytes"
                },
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
        alert['tags']['plugin_instance'] = target
        alert['tags']['warning_max'] = utils.find_warning_max(
            alert_json['Settings']['conditions'][0]['evaluator']['params'])
        result = utils.parse_target(target, self.template)
        alert['tags']['integration_id'] = result["integration_id"]
        cluster_name = utils.find_cluster_short_name(
            result["integration_id"]
        )
        alert['tags']['cluster_short_name'] = cluster_name
        alert['tags']['volume_name'] = result["volume_name"]
        return alert
