from tendrl.monitoring_integration.grafana import alert_utils


def remove_row(alert_dashboard, cluster_id, resource_type, resource_name):
    rows = alert_dashboard["dashboard"]["rows"]
    new_rows = []
    flag = True
    for row in rows:
        for target in row["panels"][0]["targets"]:
            resource = resource_name
            if resource_type == "bricks":
                hostname = resource.split(":")[0].split(
                    "|")[1].replace(".", "_")
                resource = "." + resource.split(
                    ":", 1)[1].replace("/", "|") + "."
            if resource is not None:
                if str(cluster_id) in target["target"] and str(
                        resource) in str(target["target"]):
                    if resource_type == "bricks":
                        if hostname in target["target"]:
                            flag = False
                            break
                    else:
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

    alert_dashboard = alert_utils.get_alert_dashboard(dashboard_name)
    new_rows = []
    flag = True
    rows = alert_dashboard["dashboard"]["rows"]
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
