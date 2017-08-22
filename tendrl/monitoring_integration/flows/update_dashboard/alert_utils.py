import copy


from tendrl.monitoring_integration.grafana import dashboard


def get_alert_dashboard(dashboard_name):
    slug = "alerts-tendrl-gluster-" + str(dashboard_name)
    dashboard_json = dashboard.get_dashboard(slug)
    return dashboard_json


def fetch_row(dashboard_json):

    rows = dashboard_json["dashboard"]["rows"]
    if len(rows) > 1:
        for count in xrange(1, len(rows)):
            if rows[0]["panels"][0]["title"].split("-", 1)[0] == rows[count]["panels"][0]["title"].split("-", 1)[0]:
                alert_row = copy.deepcopy(dashboard_json["dashboard"]["rows"][-count:])
                break
    else:
        alert_row = [copy.deepcopy(dashboard_json["dashboard"]["rows"][-1])]
    return alert_row


def add_volume_panel(alert_rows, cluster_id, volume_name):

    for alert_row in alert_rows:
        panel_count = alert_row["panels"][-1]["id"] + 1
        for panel in alert_row["panels"]:
            targets = panel["targets"]
            for target in targets:
                panel_target = ("tendrl" + target["target"].split("tendrl")[1].split(")")[0]).split(".")
                old_cluster_id = panel_target[panel_target.index("clusters")
                                              + 1]
                target["target"] = target["target"].replace(old_cluster_id,
                                                            str(cluster_id))
                old_volume_name = panel_target[panel_target.index("volumes") + 1]
                target["target"] = target["target"].replace(old_volume_name,
                                                            str(volume_name))
            panel["id"] = panel_count
            panel_count = panel_count + 1
            panel["title"] = panel["title"].split("-", 1)[0] + "-" + str(volume_name)


def add_cluster_panel(alert_rows, cluster_id):

    for alert_row in alert_rows:
        panel_count = alert_row["panels"][-1]["id"] + 1
        for panel in alert_row["panels"]:
            targets = panel["targets"]
            for target in targets:
                panel_target = ("tendrl" + target["target"]
                                .split("tendrl")[1].split(")")[0]).split(".")
                old_cluster_id = panel_target[panel_target.index("clusters") + 1]
                target["target"] = target["target"].replace(old_cluster_id,
                                                            str(cluster_id))
            panel["id"] = panel_count
            panel_count = panel_count + 1
            panel["title"] = panel["title"].split("-", 1)[0] + "-" + str(cluster_id)


def add_brick_panel(alert_rows, cluster_id, brick_name):

    for alert_row in alert_rows:
        panel_count = alert_row["panels"][-1]["id"] + 1
        for panel in alert_row["panels"]:
            targets = panel["targets"]
            for target in targets:
                panel_target = ("tendrl" + target["target"].split("tendrl")[1].split(")")[0]).split(".")
                old_cluster_id = panel_target[panel_target.index("clusters") + 1]
                target["target"] = target["target"].replace(old_cluster_id, str(cluster_id))
                old_brick_name = panel_target[panel_target.index("bricks") + 1]
                target["target"] = target["target"].replace(old_brick_name, str(brick_name))
            panel["id"] = panel_count
            panel_count = panel_count + 1
            panel["title"] = panel["title"].split("-", 1)[0] + "-" + str(brick_name)


def add_node_panel(alert_rows, cluster_id, node_name):

    for alert_row in alert_rows:
        panel_count = alert_row["panels"][-1]["id"] + 1
        for panel in alert_row["panels"]:
            targets = panel["targets"]
            for target in targets:
                panel_target = ("tendrl" + target["target"].split("tendrl")[1].split(")")[0]).split(".")
                old_cluster_id = panel_target[panel_target.index("clusters") + 1]
                target["target"] = target["target"].replace(old_cluster_id, str(cluster_id))
                old_node_name = panel_target[panel_target.index("nodes") + 1]
                target["target"] = target["target"].replace(old_node_name, str(node_name))
            panel["id"] = panel_count
            panel_count = panel_count + 1
            panel["title"] = panel["title"].split("-", 1)[0] + "-" + str(node_name)


def remove_row(alert_dashboard, cluster_id, resource_name):

    rows = alert_dashboard["dashboard"]["rows"]
    new_rows = []
    flag = True
    for row in rows:
        for target in row["panels"][0]["targets"]:
            # TODO(Rishubh) the case where the cluster id and resource name are on different targets
            if resource_name is not None:
                if str(cluster_id) in target["target"] and str(resource_name) in target["target"]:
                    flag = False
                    break
            else:
                if str(cluster_id) in target["target"]:
                    flag = False
                    break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows


def remove_cluster_rows(cluster_id, dashboard_name):

    alert_dashboard = get_alert_dashboard(dashboard_name)
    new_rows = []
    flag = True
    rows  = alert_dashboard["dashboard"]["rows"]
    for row in rows:
        for target in row["panels"][0]["targets"]:
            if str(cluster_id) in target["target"]:
                flag = False
                break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows
    return alert_dashboard


def create_updated_dashboard(dashboard_json, alert_rows):
    dashboard_json["dashboard"]["rows"] = dashboard_json["dashboard"]["rows"] \
                                          + alert_rows
    return dashboard_json
