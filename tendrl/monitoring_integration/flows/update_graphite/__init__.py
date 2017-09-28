import etcd
import os
import datetime


from tendrl.commons import flows
from tendrl.commons.utils import log_utils as logger


WHISPER_PATH = "/var/lib/carbon/whisper/tendrl/"

class UpdateGraphite(flows.BaseFlow):

    def run(self):
        super(UpdateGraphite, self).run()
        cluster_id = self.parameters.get("TendrlContext.integration_id")
        resource_name = str(
            self.parameters.get("Trigger.resource_name")).lower()
        resource_type = str(
            self.parameters.get("Trigger.resource_type")).lower()
        self.update_graphite(cluster_id, resource_name, resource_type)

    def update_graphite(cluster_id, resource_name, resource_type):
        if resource_type = "volume":
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id),
                                         "volumes", resource_name)
            archive_path = os.path.join(WHISPER_PATH, "clusters",
                                        str(cluster_id),
                                        "archive", "volumes")
            if not os.path.exists(archive_path):
                os.system("mkdir " + str(archive_path))
            resource_folder_name = str(resource_name) + "_" + \
                str(datetime.datetime.now().isoformat())
            archive_path = os.path.join(archive_path, resource_folder_name)
            os.system("mkdir " + str(archive_path))
            if os.path.exists(resource_path):
                os.system("mv " + str(resource_path) + " " + str(archive_path) + "/.")
            if os.path.exists(os.path.join(str(archive_path), resource_name)):
                logger.log("info", NS.get("publisher_id", None),
                           {'message': "Volume " + str(resource_name) + 
                                       "deleted from graphite"})
            else:
                 logger.log("error", NS.get("publisher_id", None),
                           {'message': "Volume " + str(resource_name) + 
                                       "deletion from graphite failed"})
        if resource_type = "brick":
            host_name = resource_name.split("|", 1)[1].split(":", 1)[0].replace(".", "_")
            brick_name = resource_name.split("|", 1)[1].split(":", 1)[1].replace("/", '\|')
            vol_name = resource_name.split("|", 1)[0]
            archive_path = os.path.join(WHISPER_PATH, "clusters",
                                        str(cluster_id),
                                        "archive", "bricks")
            if not os.path.exists(archive_path):
                os.system("mkdir " + str(archive_path))
            resource_folder_name = str(brick_name) + "_" + \
                str(datetime.datetime.now().isoformat())
            archive_path = os.path.join(archive_path, resource_folder_name)
            os.system("mkdir " + str(archive_path))
            resource_path = os.path.join(WHISPER_PATH, "clusters",
                                         str(cluster_id), "nodes",
                                         str(host_name), "bricks",
                                         str(brick_name))
            if os.path.exists(resource_path):
                os.system("mv " + str(resource_path) + " " + str(archive_path) + "/.")
            if os.path.exists(os.path.join(str(archive_path), brick_name)):
                logger.log("info", NS.get("publisher_id", None),
                           {'message': "Brick " + str(resource_name) + 
                                       "deleted from graphite"})
            else:
                 logger.log("error", NS.get("publisher_id", None),
                           {'message': "Brick " + str(resource_name) + 
                                       "deletion from graphite failed"})

