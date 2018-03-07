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


class BrickHandler(AlertHandler):

    handles = 'brick'
    representive_name = 'brick_utilization'

    def __init__(self):
        AlertHandler.__init__(self)
        self.template = "tendrl.clusters.{cluster_id}.nodes."\
            "{host_name}.bricks.{brick_path}.utilization."\
            "percent-percent_bytes"

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
            alert['severity'] = constants.TENDRL_GRAFANA_SEVERITY_MAP[
                alert_json['State']]
            alert['significance'] = constants.SIGNIFICANCE_HIGH
            alert['pid'] = utils.find_grafana_pid()
            alert['source'] = constants.ALERT_SOURCE
            alert['tags']['cluster_name'] = utils.find_cluster_name(
                alert['tags']['integration_id'])
            if alert['severity'] == "WARNING":
                alert['tags']['message'] = (
                    "Brick utilization of %s:%s in "
                    "cluster %s is %s %% which is above %s"
                    " threshold (%s %%)" % (
                        alert['tags']['fqdn'],
                        alert['tags']['brick_path'],
                        alert['tags']['integration_id'],
                        alert['current_value'],
                        alert['severity'],
                        alert['tags']['warning_max']
                    )
                )
            elif alert['severity'] == "INFO":
                alert['tags']['message'] = (
                    "Brick utilization of %s:%s in "
                    "cluster %s is back normal" % (
                        alert['tags']['fqdn'],
                        alert['tags']['brick_path'],
                        alert['tags']['integration_id']
                    )
                )
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
            evalMatches:[{
              metric: "tendrl.clusters.ab3b125e-4769-4071-
                      a349-e82b380c11f4.nodes.{host_name}.
                      bricks.|root|gluster_bricks
                      |vol1_b2.utilization.percent-percent_bytes",
              tags: null,
              value: 15.614466017499998
            }]
          },
          Settings: {
            conditions: - [{
              evaluator: - {
                params: - [15],
                type: "gt"
              },
              query : {
                model : {
                  target: "tendrl.clusters.ab3b125e-4769-
                          4071-a349-e82b380c11f4.nodes.dhcp42-208_lab_eng_blr_
                          redhat_com.bricks.|root|
                          gluster_bricks|vol1_b2.utilization.percent-
                          percent_bytes"
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
        alert['tags']['plugin_instance'] = target
        alert['tags']['warning_max'] = utils.find_warning_max(
            alert_json['Settings']['conditions'][0]['evaluator']['params'])
        result = utils.parse_target(target, self.template)
        alert['tags']['integration_id'] = result["cluster_id"]
        alert["tags"]["fqdn"] = result["host_name"].replace("_", ".")
        alert['tags']['brick_path'] = result["brick_path"]
        return alert
