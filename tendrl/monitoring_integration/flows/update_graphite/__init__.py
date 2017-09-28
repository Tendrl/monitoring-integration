import etcd
import os
import datetime


from tendrl.commons import flows
from tendrl.commons.utils import log_utils as logger
from tendrl.commons.utils import etcd_utils
from tendrl.monitoring_integration.grafana import create_dashboards


WHISPER_PATH = "/var/lib/carbon/whisper/tendrl/"

class UpdateGraphite(flows.BaseFlow):

    def run(self):
        super(UpdateGraphite, self).run()
        cluster_id = self.parameters.get("TendrlContext.integration_id")
        resource_name = str(
            self.parameters.get("Trigger.resource_name")).lower()
        resource_type = str(
            self.parameters.get("Trigger.resource_type")).lower()
        import pdb; pdb.set_trace()
        self.update_graphite(cluster_id, resource_name,
                             resource_type.lower())

    def update_graphite(self, cluster_id, resource_name, resource_type):
        if resource_type == "volume":
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id),
                                         "volumes", resource_name)
            archive_path = os.path.join(WHISPER_PATH, "clusters",
                                        str(cluster_id),
                                        "archive", "volumes")
            if not os.path.exists(archive_path):
                os.system("mkdir -p " + str(archive_path))
            resource_folder_name = str(resource_name) + "_" + \
                str(datetime.datetime.now().isoformat())
            archive_path = os.path.join(archive_path, resource_folder_name)
            if os.path.exists(resource_path):
                os.system("mv " + str(resource_path) + " " +
                          str(archive_path))
            if os.path.exists(os.path.join(str(archive_path),
                                           resource_name)):
                logger.log("info", NS.get("publisher_id", None),
                           {'message': "Volume " + str(resource_name) + 
                                       "deleted from graphite"})
            else:
                 logger.log("error", NS.get("publisher_id", None),
                           {'message': "Volume " + str(resource_name) +
                                       "deletion from graphite failed"})
        if resource_type == "brick":
            host_name = resource_name.split("|",
                                            1)[1].split(":",
                                                        1)[0].replace(".",
                                                                      "_")
            brick_name = resource_name.split("|",
                                             1)[1].split(":",
                                                         1)[1].replace("/",
                                                                       '\|')
            vol_name = resource_name.split("|", 1)[0]
            archive_path = os.path.join(WHISPER_PATH, "clusters",
                                        str(cluster_id),
                                        "archive", "bricks")
            if not os.path.exists(archive_path):
                os.system("mkdir -p " + str(archive_path))
            resource_folder_name = str(brick_name) + "_" + \
                str(datetime.datetime.now().isoformat())
            archive_path = os.path.join(archive_path, resource_folder_name)
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id), "nodes",
                                         str(host_name), "bricks",
                                         str(brick_name))
            brick_path = os.path.join(
                WHISPER_PATH,
                "clusters",
                str(cluster_id),
                "nodes",
                str(host_name),
                "bricks",
                resource_name.split("|", 1)[1].split(":", 1)[1].replace("/", "|")
            )
            if os.path.exists(brick_path):
                ret_val = os.system("mv " + str(resource_path) + " " +
                          str(archive_path))
                if ret_val is 0:
                    logger.log("info", NS.get("publisher_id", None),
                              {'message': "Brick " + str(resource_name) + 
                                       "deleted from graphite"})
                else:
                     logger.log("error", NS.get("publisher_id", None),
                               {'message': "Brick " + str(resource_name) + 
                                       "deletion from graphite failed"})
            archive_path = os.path.join(archive_path,
                                        "volumes", vol_name)
            os.system("mkdir -p " + str(archive_path))
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id), "volumes",
                                         str(vol_name), "nodes",
                                         str(host_name), "bricks",
                                         str(brick_name))
            brick_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id), "volumes",
                                         str(vol_name), "nodes",
                                         str(host_name), "bricks",
                                         resource_name.split("|", 1)[1].split(":", 1)[1].replace("/", "|"))
            if os.path.exists(brick_path):
                ret_val = os.system("mv " + str(resource_path) + " " +
                                 str(archive_path))
                if ret_val is 0:
                    logger.log("info", NS.get("publisher_id", None),
                              {'message': "Brick " + str(resource_name) + 
                                       "deleted from graphite"})
                else:
                    logger.log("error", NS.get("publisher_id", None),
                              {'message': "Brick " + str(resource_name) + 
                                       "deletion from graphite failed"})
        if resource_type == "host":
            host_name = resource_name.replace(".", "_")
            volume_affected_list = []
            volume_key = os.path.join("clusters", str(cluster_id), "Volumes")
            volume_list = create_dashboards.get_resource_keys("", volume_key)
            for volume_id in volume_list:
                flag = False
                single_volume_key = os.path.join(volume_key, volume_id,
                                                 "Bricks")
                subvolume_list = create_dashboards.get_resource_keys("", single_volume_key)
                for subvolume in subvolume_list:
                    subvolume_brick_key = os.path.join(single_volume_key,
                                                       subvolume)
                    brick_list = create_dashboards.get_resource_keys("", subvolume_brick_key)
                    if flag:
                        flag = False
                        continue
                    for brick in brick_list:
                        subvolume_hostname = brick.split(":",
                                                         1)[0].replace(".",
                                                                       "_")
                        if host_name == subvolume_hostname:
                            volume_key = os.path.join(volume_key, volume_id,
                                                      "name")
                            try:
                                volume_name = etcd_utils.read(volume_key).value
                                volume_affected_list.append(volume_name)
                            except etcd.EtcdKeyNotFound:
                                pass
                            flag = True
                            continue
            archive_path = os.path.join(WHISPER_PATH, "clusters",
                                        str(cluster_id),
                                        "archive", "nodes")
            if not os.path.exists(archive_path):
                os.system("mkdir -p " + str(archive_path))
            resource_folder_name = str(host_name) + "_" + \
                str(datetime.datetime.now().isoformat())
            archive_path = os.path.join(archive_path, resource_folder_name)
            os.system("mkdir -p " + str(archive_path))
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id), "nodes",
                                         str(host_name))
            if os.path.exists(resource_path):
                ret_val = os.system("mv " + str(resource_path) + " " +
                                    str(archive_path))
                if ret_val is 0:
                    logger.log("info", NS.get("publisher_id", None),
                               {'message': "Host " + str(resource_name) + 
                                       "deleted from graphite"})
                else:
                     logger.log("error", NS.get("publisher_id", None),
                                {'message': "Host " + str(resource_name) + 
                                       "deletion from graphite failed"})
            for vol_name in volume_affected_list:
                archive_path = os.path.join(archive_path,
                                            "volumes", vol_name)
                os.system("mkdir -p " + str(archive_path))
                resource_path = os.path.join(WHISPER_PATH, "clusters",
                                             str(cluster_id), "volumes",
                                             str(vol_name), "nodes",
                                             str(host_name))
                if os.path.exists(resource_path):
                    ret_val = os.system("mv " + str(resource_path) + " " +
                                     str(archive_path))
                    if ret_val is 0:
                        logger.log("info", NS.get("publisher_id", None),
                                   {'message': "Host " + str(resource_name) +
                                       "deleted from graphite"})
                    else:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Host " + str(resource_name) +
                                    "deletion from graphite failed"})
