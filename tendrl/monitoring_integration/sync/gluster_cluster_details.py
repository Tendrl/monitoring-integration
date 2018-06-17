import etcd

from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger


def get_cluster_details():
    cluster_details = {}
    try:
        clusters = NS.tendrl.objects.Cluster().load_all()
        for cluster in clusters:
            if cluster.is_managed in ['yes', 'Yes', 'YES']:
                integration_id = cluster.integration_id
                cluster_details[integration_id] = {}
                # Get node details
                cluster_details[integration_id]["hosts"] = get_node_details(
                    integration_id
                )
                # Get volume details
                cluster_details[integration_id]["volumes"] = \
                    get_volumes_details(
                        integration_id
                    )
                # Get brick details from subvolumes
                cluster_details[integration_id]["bricks"] = get_brick_details(
                    integration_id
                )
                cluster_details[integration_id]["short_name"] = \
                    cluster.short_name
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
            if _cnc.is_managed.lower() == "yes":
                node_details.append(_cnc)
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


def get_brick_details(integration_id):
    brick_details = []
    try:
        nodes = etcd_utils.read(
            "/clusters/%s/Bricks/all" % integration_id
        )
        for node in nodes.leaves:
            bricks = NS.tendrl.objects.GlusterBrick(
                integration_id,
                fqdn=node.key.split("/")[-1]
            ).load_all()
            for brick in bricks:
                if str(brick.deleted).lower() != 'true':
                    brick_details.append(brick)
    except (KeyError, etcd.EtcdKeyNotFound) as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {
                'message': "Error while fetching brick details for"
                "cluster {}".format(integration_id) + str(ex)
            }
        )
    return brick_details


def get_volumes_details(integration_id):
    volume_details = []
    _volumes = NS.tendrl.objects.GlusterVolume(
        integration_id=integration_id
    ).load_all()
    for _volume in _volumes:
        if str(_volume.deleted).lower() != 'true' and \
                _volume.name is not None:
            volume_details.append(_volume)
    return volume_details
