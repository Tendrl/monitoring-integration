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
from tendrl.monitoring_integration.grafana import constants as \
    grafana_constants


class BrickHandler(AlertHandler):

    handles = 'brick'
    representive_name = 'brick_utilization'

    def __init__(self):
        AlertHandler.__init__(self)
        self.template = "tendrl[.]clusters[.]{integration_id}[.]nodes[.]"\
            "{host_name}[.]bricks[.]{brick_path}[.]"

    def format_alert(self, alert_json):
        alert = self.parse_alert_metrics(alert_json)
        try:
            alert["alert_id"] = None
            alert["node_id"] = utils.find_node_id(
                alert['tags']['integration_id'],
                alert['tags']['fqdn']
            )
            alert["time_stamp"] = tendrl_now().isoformat()
            alert["resource"] = self.representive_name
            alert['alert_type'] = constants.ALERT_TYPE
            alert['significance'] = constants.SIGNIFICANCE_HIGH
            alert['pid'] = utils.find_grafana_pid()
            alert['source'] = constants.ALERT_SOURCE
            alert['tags']['cluster_name'] = utils.find_cluster_name(
                alert['tags']['integration_id'])
            alert["tags"]["volume_name"] = utils.find_volume_name(
                alert['tags']['integration_id'],
                alert['tags']['fqdn'].replace('_', '.'),
                alert['tags']['brick_path'].strip(":").replace(
                    grafana_constants.BRICK_PATH_SEPARATOR, '_'
                )
            )
            if alert_json['State'] == constants.GRAFANA_ALERT:
                if "critical" in alert_json['Name'].lower():
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['critical']
                else:
                    alert['severity'] = \
                        constants.TENDRL_SEVERITY_MAP['warning']
                # Modify brick path symbol to slash(/) in alert message
                alert['tags']['message'] = (
                    "Brick utilization on %s:%s in %s "
                    "at %s %% and nearing full capacity" % (
                        alert['tags']['fqdn'],
                        alert['tags']['brick_path'].replace(
                            grafana_constants.BRICK_PATH_SEPARATOR, "/"
                        ),
                        alert["tags"]["volume_name"],
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
                # Modify brick path symbol to slash(/) in alert message
                alert['tags']['message'] = (
                    "Brick utilization of %s:%s in %s "
                    "back to normal" % (
                        alert['tags']['fqdn'],
                        alert['tags']['brick_path'].replace(
                            grafana_constants.BRICK_PATH_SEPARATOR, "/"
                        ),
                        alert["tags"]["volume_name"]
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
        # For alert backward compatibility
        alert['tags']['plugin_instance'] = target.replace(
            grafana_constants.BRICK_PATH_SEPARATOR, "|"
        )
        alert['tags']['warning_max'] = utils.find_warning_max(
            alert_json['Settings']['conditions'][0]['evaluator']['params'])
        result = utils.parse_target(target, self.template)
        alert['tags']['integration_id'] = result["integration_id"]
        cluster_name = utils.find_cluster_short_name(
            result["integration_id"]
        )
        alert['tags']['cluster_short_name'] = cluster_name
        alert["tags"]["fqdn"] = result["host_name"].replace("_", ".")
        alert['tags']['brick_path'] = result["brick_path"]
        return alert
