import ConfigParser
import copy
import os

from tendrl.commons.utils import log_utils as logger


def archive(
    resource_path,
    archive_path,
    resource_name,
    resource_type
):
    ret_val = os.system(
        "mv " + str(resource_path) + " " + str(archive_path)
    )
    if ret_val is 0:
        msg = "%s - %s deleted from graphite" % (
            resource_type, resource_name
        )
        logger.log("info", NS.get("publisher_id", None),
                   {'message': msg})
    else:
        msg = "%s - %s deleted from graphite failed" % (
            resource_type, resource_name
        )
        logger.log("error", NS.get("publisher_id", None),
                   {'message': msg})


def get_data_dir_path():
    carbon_path = "/etc/carbon/carbon.conf"
    if not os.path.exists(carbon_path):
        return None
    carbon_config = ConfigParser.ConfigParser()
    carbon_config.read(carbon_path)
    try:
        whisper_path = str(carbon_config.get("cache", "local_data_dir"))
        whisper_path = os.path.join(whisper_path, "tendrl/")
        return whisper_path
    except KeyError:
        return None


def _add_metrics(objects, obj_name, metric, resource):

    metrics = []
    for obj in objects[obj_name]["attrs"]:
        if obj == "name" or obj == "fqdn":
            continue
        local_metric = copy.deepcopy(metric)
        try:
            if isinstance(resource[obj], dict):
                for key, value in resource[obj].items():
                    try:
                        if key == "details":
                            continue
                        new_metric = local_metric + "." + str(
                            obj) + "." + str(key)
                        metric_value = str(value)
                        final_metric = {new_metric: metric_value}
                        metrics.append(copy.deepcopy(final_metric))
                    except (AttributeError, KeyError) as ex:
                        logger.log(
                            "error",
                            NS.get("publisher_id", None),
                            {
                                'message': "Failed to fetch key {0} of attr "
                                "{1}".format(key, obj) + str(ex)
                            }
                        )
            else:
                metric_value = str(resource[obj])
                local_metric = local_metric + "." + str(obj)
                final_metric = {local_metric: metric_value}
                metrics.append(copy.deepcopy(final_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "debug",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to fetch attribute "
                    "{}".format(obj) + str(ex)
                }
            )
            pass

    return metrics


def node_wise_brick_count(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.nodes.$node_name.brick_count."
        "total.$brick_total_count",
        "clusters.$integration_id.nodes.$node_name.brick_count."
        "down.$brick_down_count",
        "clusters.$integration_id.nodes.$node_name.brick_count."
        "up.$brick_up_count"
    ]
    metrics = []
    for metric in local_metrics:
        metric = metric.replace(
            "$integration_id",
            str(cluster_detail["integration_id"])
        )
        for node in cluster_detail["Node"]:
            try:
                local_metric = metric.replace(
                    "$node_name",
                    node["fqdn"].replace(".", "_")
                )
                local_metric = local_metric.replace(
                    local_metric.rsplit(".", 1)[1],
                    str(node[str(local_metric.rsplit(".", 1)[1].replace(
                        "$", ""))]))
                metrics.append(copy.deepcopy(local_metric))
            except (AttributeError, KeyError) as ex:
                logger.log(
                    "debug",
                    NS.get("publisher_id", None),
                    {
                        'message': "Failed to create brick metric "
                        "for Node: {0} "
                        "Metric: {1}".format(node, metric) + str(ex)
                    }
                )
    return metrics


def cluster_wise_brick_count(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.brick_count.total.$brick_total_count",
        "clusters.$integration_id.brick_count.down.$brick_down_count",
        "clusters.$integration_id.brick_count.up.$brick_up_count"
    ]
    metrics = []
    for metric in local_metrics:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"])
            )
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(cluster_detail[str(local_metric.rsplit(
                    ".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create cluster metric {0} "
                    "for cluster {1}".format(metric, str(
                        cluster_detail["integration_id"])) + str(ex)
                }
            )
    return metrics


def volume_wise_brick_count(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.volumes.$volume_name."
        "brick_count.total.$total",
        "clusters.$integration_id.volumes.$volume_name."
        "brick_count.down.$down",
        "clusters.$integration_id.volumes.$volume_name."
        "brick_count.up.$up"
    ]
    metrics = []
    for metric in local_metrics:
        metric = metric.replace(
            "$integration_id",
            str(cluster_detail["integration_id"])
        )
        for volume in cluster_detail["Volume"]:
            try:
                local_metric = metric.replace(
                    "$volume_name",
                    volume["name"]
                )
                local_metric = local_metric.replace(
                    local_metric.rsplit(".", 1)[1],
                    str(cluster_detail["volume_level_brick_count"][
                        str(volume["name"])][str(local_metric.rsplit(
                            ".", 1)[1].replace("$", ""))]))
                metrics.append(copy.deepcopy(local_metric))
            except (AttributeError, KeyError) as ex:
                logger.log(
                    "error", NS.get("publisher_id", None),
                    {
                        'message': "Failed to create volume metric {0} "
                        "for Volume :{1}".format(
                            metric, volume["name"]) + str(ex)
                    }
                )
    return metrics


def node_count(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.nodes_count.total.$node_total_count",
        "clusters.$integration_id.nodes_count.down.$node_down_count",
        "clusters.$integration_id.nodes_count.up.$node_up_count"
    ]
    metrics = []
    for metric in local_metrics:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"])
            )
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(cluster_detail[str(local_metric.rsplit(
                    ".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
                logger.log(
                    "error",
                    NS.get("publisher_id", None),
                    {
                        'message': "Failed to create cluster metric {0} "
                        "for cluster {1}".format(metric, str(
                            cluster_detail["integration_id"])) + str(ex)
                    }
                )
    return metrics


def volume_count(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.volume_count.total.$volume_total_count",
        "clusters.$integration_id.volume_count.down.$volume_down_count",
        "clusters.$integration_id.volume_count.up.$volume_up_count",
        "clusters.$integration_id.volume_count.partial.$volume_partial_count",
        "clusters.$integration_id.volume_count.degraded.$volume_degraded_count"
    ]
    metrics = []
    for metric in local_metrics:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"])
            )
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(cluster_detail[str(local_metric.rsplit(
                    ".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create cluster metric "
                    "{0} for cluster {1}".format(metric, str(
                        cluster_detail["integration_id"])) + str(ex)
                }
            )
    return metrics


def volume_wise_brick_status(cluster_detail):
    metric = "clusters.$integration_id.volumes.$volume_name." \
        "nodes.$node_name.bricks.$brick_name.status.$status"
    volume_names = []
    for volume in cluster_detail["Volume"]:
        volume_names.append(volume["name"])
    metrics = []
    for brick in cluster_detail["Brick"]:
        try:
            if brick["vol_name"] not in volume_names:
                continue
        except (KeyError, AttributeError):
            continue
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"]))
            local_metric = local_metric.replace(
                "$volume_name", brick["vol_name"])
            local_metric = local_metric.replace(
                "$node_name", brick["host_name"])
            local_metric = local_metric.replace(
                "$brick_name",
                brick["brick_name"].replace("/", "|"))
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(brick[str(local_metric.rsplit(
                    ".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "debug",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create brick metric {0} "
                    "for Brick :{1}".format(metric, brick) + str(ex)
                }
            )
    return metrics


def node_wise_brick_status(cluster_detail):
    metric = "clusters.$integration_id.nodes.$node_name." \
        "bricks.$brick_name.status.$status"
    metrics = []
    for brick in cluster_detail["Brick"]:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"]))
            local_metric = local_metric.replace(
                "$node_name",
                brick["host_name"]
            )
            local_metric = local_metric.replace(
                "$brick_name",
                brick["brick_name"].replace("/", "|")
            )
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(brick[str(local_metric.rsplit(
                    ".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "debug",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create brick metric {0} "
                    "for Brick :{1}".format(metric, brick) + str(ex)
                }
            )
    return metrics


def cluster_status(cluster_detail):
    local_metrics = ["clusters.$integration_id.status.$status"]
    metrics = []
    for metric in local_metrics:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"])
            )
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(cluster_detail["Cluster"][0][
                    "GlobalDetails"]["status"]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "debug",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create cluster metric {0} "
                    "for cluster {1}".format(metric, str(
                        cluster_detail["integration_id"])) + str(ex)
                })
    return metrics


def georep_status(cluster_detail):
    local_metrics = [
        "clusters.$integration_id.georep.total.$total",
        "clusters.$integration_id.georep.up.$up",
        "clusters.$integration_id.georep.down.$down",
        "clusters.$integration_id.georep.partial.$partial",
        "clusters.$integration_id.georep.stopped.$stopped",
        "clusters.$integration_id.georep.paused.$paused",
        "clusters.$integration_id.georep.created.$created"
    ]
    metrics = []
    for metric in local_metrics:
        try:
            local_metric = metric.replace(
                "$integration_id",
                str(cluster_detail["integration_id"]))
            local_metric = local_metric.replace(
                local_metric.rsplit(".", 1)[1],
                str(cluster_detail["geo_rep"][str(
                    local_metric.rsplit(".", 1)[1].replace("$", ""))]))
            metrics.append(copy.deepcopy(local_metric))
        except (AttributeError, KeyError) as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {
                    'message': "Failed to create cluster metric {0} "
                    "for cluster {1}".format(metric, str(
                        cluster_detail["integration_id"])) + str(ex)
                }
            )
    return metrics


def miscellaneous_metrics(cluster_details):
    metrics = []
    for cluster_detail in cluster_details:
        metrics.extend(node_wise_brick_count(cluster_detail))
        metrics.extend(cluster_wise_brick_count(cluster_detail))
        metrics.extend(volume_wise_brick_count(cluster_detail))
        metrics.extend(node_count(cluster_detail))
        metrics.extend(volume_count(cluster_detail))
        metrics.extend(volume_wise_brick_status(cluster_detail))
        metrics.extend(node_wise_brick_status(cluster_detail))
        metrics.extend(cluster_status(cluster_detail))
        metrics.extend(georep_status(cluster_detail))
    return metrics


def create_metrics(objects, cluster_details):
    metrics = []
    for obj in objects:
        try:
            for metric in objects[obj]["metric"]:
                for cluster_detail in cluster_details:
                    local_metric = copy.deepcopy(metric)
                    local_metric = local_metric.replace(
                        "$integration_id",
                        str(cluster_detail["integration_id"])
                    )
                    if "$node_name" in metric and "$brick_name" not in metric:
                        for node in cluster_detail["Node"]:
                            try:
                                node_metric = copy.deepcopy(local_metric)
                                node_metric = node_metric.replace(
                                    "$node_name",
                                    node["fqdn"].replace(".", "_")
                                )
                                node_metric = _add_metrics(
                                    objects, obj, node_metric, node)
                                metrics = metrics + copy.deepcopy(node_metric)
                            except (AttributeError, KeyError) as ex:
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Failed to fetch Node {} "
                                        "details ".format(node) + str(ex)})
                    elif "$volume_name" in metric:
                        for volume in cluster_detail["Volume"]:
                            try:
                                volume_metric = copy.deepcopy(local_metric)
                                volume_metric = volume_metric.replace(
                                    "$volume_name", volume["name"])
                                volume_metric = _add_metrics(
                                    objects, obj, volume_metric, volume)
                                metrics = metrics + copy.deepcopy(
                                    volume_metric)
                            except (AttributeError, KeyError) as ex:
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Failed to fetch Volume {} "
                                        "details ".format(volume) + str(ex)
                                    }
                                )

        except (AttributeError, KeyError) as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Failed to fetch all metrics " + str(ex)})
    count_metrics = miscellaneous_metrics(cluster_details)
    misc_metrics = []
    for metric in count_metrics:
        temp_metric = {}
        temp_metric[metric.rsplit(".", 1)[0]] = metric.rsplit(".", 1)[1]
        misc_metrics.append(copy.deepcopy(temp_metric))
    metrics = metrics + misc_metrics
    return metrics
