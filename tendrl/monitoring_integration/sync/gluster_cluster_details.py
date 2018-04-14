import copy
import etcd

from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import utils


def get_cluster_details(integration_id):
    cluster_details = {}
    try:
        _cluster = NS.tendrl.objects.Cluster(
            integration_id=integration_id
        ).load()
        if _cluster.is_managed in ["yes", "YES"]:
            cluster_details["integration_id"] = integration_id
            # Get node details
            cluster_details["hosts"] = get_node_details(integration_id)
            # Get volume details
            cluster_details["volumes"] = get_volumes_details(integration_id)
            # Get brick details from subvolumes
            cluster_details["bricks"] = get_brick_details(
                cluster_details["volumes"],
                integration_id
            )
    except (etcd.EtcdKeyNotFound, KeyError) as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {'message': str(ex)}
        )
    return cluster_details


def get_node_details(integration_id):
    node_details = []
    try:
        _cluster_node_ids = etcd_utils.read(
            "/clusters/%s/nodes" % integration_id
        )
        for _node_id in _cluster_node_ids.leaves:
            _cnc = NS.tendrl.objects.ClusterNodeContext(
                integration_id=integration_id,
                node_id=_node_id.key.split('/')[-1]
            ).load()
            node = {
                "fqdn": _cnc.fqdn
            }
            node_details.append(node)
    except etcd.EtcdKeyNotFound as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {
                "message": "Error while fetching node details."
                " Error: %s" % str(ex)
            }
        )
    return node_details


def get_brick_path(brick_info, integration_id):
    _brick = NS.tendrl.objects.GlusterBrick(
        integration_id=integration_id,
        brick_dir=brick_info.replace(":_", "/")
    ).load()
    return _brick.brick_path.split(":")[1].replace(
        "/", "|"
    )


def get_brick_details(volumes, integration_id):
    brick_details = []
    try:
        for volume in volumes:
            for subvolume in volume["subvolume"]:
                for brick_info in subvolume["bricks"]:
                    brick = {}
                    brick["hostname"] = brick_info.split(":")[0]
                    brick["vol_id"] = volume["vol_id"]
                    brick["vol_name"] = volume["name"]
                    brick["brick_path"] = get_brick_path(
                        brick_info,
                        integration_id
                    )
                    brick["sds_name"] = constants.GLUSTER
                    brick["integration_id"] = integration_id
                    brick["resource_name"] = "%s|%s:%s" % (
                        str(brick["vol_name"]),
                        brick["hostname"],
                        brick["brick_path"].replace("|", "/")
                    )
                    brick_details.append(brick)
    except (KeyError, etcd.EtcdKeyNotFound) as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {
                'message': "Error while brick details for"
                "brick {}".format(subvolume) + str(ex)
            }
        )
    return brick_details


def get_volumes_details(integration_id):
    volume_details = []
    _volumes = NS.tendrl.objects.GlusterVolume(
        integration_id=integration_id
    ).load_all()
    for _volume in _volumes:
        if _volume.deleted not in ['true', 'True', 'TRUE']:
            volume_data = {
                'name': _volume.name,
                'vol_id': _volume.vol_id
            }
            subvolume_key = 'clusters/%s/Volumes/%s' % (
                integration_id,
                _volume.vol_id
            )
            subvolume_details = get_subvolume_details(subvolume_key)
            volume_data['subvolume'] = subvolume_details
            volume_details.append(volume_data)
    return volume_details


def get_subvolume_details(key):
    subvolume_brick_details = []
    try:
        subvolumes = utils.get_resource_keys(key, "Bricks")
        for subvolume in subvolumes:
            try:
                subvolume_details = {}
                subvolume_details["subvolume"] = ""
                subvolume_details["bricks"] = []
                subvolume_details["subvolume"] = subvolume
                brick_list = utils.get_resource_keys(
                    key + "/" + "Bricks", subvolume
                )
                subvolume_details["bricks"] = brick_list
                subvolume_brick_details.append(
                    copy.deepcopy(subvolume_details)
                )
            except (etcd.EtcdKeyNotFound, KeyError):
                continue
    except etcd.EtcdKeyNotFound as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {
                'message': "Error while fetching "
                "subvolumes" + str(ex)
            }
        )
    return subvolume_brick_details
