ALERT_ORG = "Alert_dashboard"
MAIN_ORG = "Main Org."
PATH_PREFIX = "/etc/tendrl/monitoring-integration"
DASHBOARD_PATH = '/grafana/dashboards'
GLUSTER = "gluster"
RHGS = "RHGS"
HEADERS = {"Accept": "application/json",
           "Content-Type": "application/json"
           }
GLUSTER_DASHBOARDS = ["volumes", "hosts", "bricks"]
ALERT_SEVERITY = ["Warning", "Critical"]
MAX_PANELS_IN_ROW = 7
HOST_TEMPLATE = "tendrl[.]names[.]{integration_id}[.]nodes[.]{host_name}[.]"
BRICK_TEMPLATE = "tendrl[.]names[.]{integration_id}[.]nodes[.]" \
    "{host_name}[.]bricks[.]{brick_path}[.]"
VOLUME_TEMPLATE = "tendrl[.]names[.]{integration_id}[.]volumes[.]" \
    "{volume_name}[.]"
