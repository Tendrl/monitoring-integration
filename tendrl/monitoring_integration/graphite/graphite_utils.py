import copy


from tendrl.commons.utils import log_utils as logger


def _add_metrics(objects, obj_name, metric, resource):

    metrics = []
    for obj in objects[obj_name]["attrs"]:
        if obj == "name" or obj == "fqdn":
            continue
        local_metric = copy.deepcopy(metric)
        try:
            if isinstance(resource[obj],dict):
                for key, value in resource[obj].items():
                    if key == "details":
                        continue
                    new_metric = local_metric + "." + str(obj) + "." + str(key)
                    metric_value = str(value)
                    final_metric = {new_metric : metric_value}
                    metrics.append(copy.deepcopy(final_metric))
            else:
                metric_value = str(resource[obj])
                if  str(obj) == "status" and "volumes" in metric:
                    obj = "vol_status"
                local_metric = local_metric + "." + str(obj)
                final_metric = {local_metric : metric_value}
                metrics.append(copy.deepcopy(final_metric))
        except {AttributeError,KeyError} as ex:
            logger.log("error", NS.get("publisher_id", None),
                      {'message': str(ex)})
            pass

    return metrics


def create_metrics(objects, cluster_details):
    metrics = []
    for obj in objects:
        try:
            for metric in objects[obj]["metric"]:
                for cluster_detail in cluster_details:
                    local_metric = copy.deepcopy(metric)
                    local_metric = local_metric.replace("$integration_id", str(cluster_detail.integration_id))

                    if "$brick_name" in local_metric and "$node_name" in local_metric:
                        for brick in cluster_detail.details["Brick"]:
                            brick_metric = copy.deepcopy(local_metric)
                            brick_metric = brick_metric.replace("$brick_name", brick["brick_path"].split(":")[1].replace("/", "|"))
                            brick_metric = brick_metric.replace("$node_name", brick["brick_path"].split(":")[0].replace(".", "_"))
                            brick_metric = _add_metrics(objects, obj, brick_metric, brick)
                            metrics = metrics + copy.deepcopy(brick_metric)
                    elif "$node_name" in metric:
                        for node in cluster_detail.details["Node"]:
                            node_metric = copy.deepcopy(local_metric)
                            node_metric = node_metric.replace("$node_name", node["fqdn"].replace(".", "_"))
                            node_metric = _add_metrics(objects, obj, node_metric, node)
                            metrics = metrics + copy.deepcopy(node_metric)
                    elif "$volume_name" in metric:
                        for volume in cluster_detail.details["Volume"]:
                            volume_metric = copy.deepcopy(local_metric)
                            volume_metric = volume_metric.replace("$volume_name", volume["name"])
                            volume_metric = _add_metrics(objects, obj, volume_metric, volume)
                            metrics = metrics + copy.deepcopy(volume_metric)
                    else:
                        for cluster in cluster_detail.details["GlobalDetails"]:
                            cluster_metric = _add_metrics(objects, obj, local_metric, cluster)
                            metrics = metrics + copy.deepcopy(cluster_metric)   
        except (AttributeError,KeyError) as ex:
            logger.log("error", NS.get("publisher_id", None),
                     {'message': str(ex)})
    return metrics

