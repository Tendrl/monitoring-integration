import ConfigParser
import datetime
import etcd
import os

from tendrl.commons import flows
from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import create_dashboards


class DeleteResourceFromGraphite(flows.BaseFlow):

    def run(self):
        super(DeleteResourceFromGraphite, self).run()
        integration_id = self.parameters.get("TendrlContext.integration_id")
        resource_name = str(
            self.parameters.get("Trigger.resource_name")
        ).lower()
        resource_type = str(
            self.parameters.get("Trigger.resource_type")).lower()
        self.update_graphite(
            integration_id,
            resource_name,
            resource_type.lower()
        )

    def get_data_dir_path(self):
        carbon_path = "/etc/tendrl/monitoring-integration/carbon.conf"
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

    def delete_brick_details(
        self,
        integration_id,
        resource_name,
        whisper_path
    ):
        host_name = resource_name.split("|", 1)[1].split(
            ":", 1
        )[0].replace(".", "_")
        brick_name = resource_name.split("|", 1)[1].split(
            ":", 1)[1].replace("/", "|")
        vol_name = resource_name.split("|", 1)[0]
        archive_base_path = os.path.join(
            whisper_path, "clusters", str(integration_id), "archive", "bricks"
        )
        archive_time = str(datetime.datetime.now().isoformat())
        if not os.path.exists(archive_base_path):
            os.makedirs(str(archive_base_path))
        archive_path = os.path.join(
            archive_base_path,
            str(brick_name).replace("|", "\|") + "_" + archive_time
        )
        resource_path = os.path.join(
            whisper_path, "clusters", str(integration_id), "nodes",
            str(host_name), "bricks", str(brick_name).replace("|", "\|"))
        brick_path = os.path.join(
            whisper_path, "clusters", str(integration_id), "nodes",
            str(host_name), "bricks", str(brick_name)
        )
        if os.path.exists(brick_path):
            ret_val = os.system(
                "mv " + str(resource_path) + " " + str(archive_path)
            )
            if ret_val is 0:
                logger.log(
                    "info",
                    NS.get("publisher_id", None),
                    {
                        'message': "Brick " + str(resource_name) +
                        "deleted from graphite"
                    }
                )
            else:
                logger.log(
                    "error",
                    NS.get("publisher_id", None),
                    {
                        'message': "Brick " + str(resource_name) +
                        "deletion from graphite failed"
                    }
                )
        archive_path = os.path.join(
            archive_base_path,
            str(brick_name) + "_" + archive_time,
            "volumes",
            vol_name
        )
        os.makedirs(str(archive_path))
        archive_path = os.path.join(
            archive_base_path,
            str(brick_name).replace("|", "\|") + "_" + archive_time,
            "volumes",
            vol_name
        )
        resource_path = os.path.join(
            whisper_path,
            "clusters",
            str(integration_id), "volumes",
            str(vol_name), "nodes",
            str(host_name), "bricks",
            str(brick_name).replace("|", "\|")
        )
        brick_path = os.path.join(
            whisper_path, "clusters",
            str(integration_id), "volumes",
            str(vol_name), "nodes",
            str(host_name), "bricks",
            str(brick_name)
        )
        if os.path.exists(brick_path):
            ret_val = os.system(
                "mv " + str(resource_path) + " " + str(archive_path)
            )
            if ret_val is 0:
                logger.log(
                    "info",
                    NS.get("publisher_id", None),
                    {
                        'message': "Brick " + str(resource_name) +
                        "deleted from graphite"
                    }
                )
            else:
                logger.log(
                    "error",
                    NS.get("publisher_id", None),
                    {
                        'message': "Brick " + str(resource_name) +
                        "deletion from graphite failed"
                    }
                )

    def delete_volume_details(
        self,
        integration_id,
        resource_name,
        whisper_path
    ):
        resource_path = os.path.join(
            whisper_path,
            "clusters",
            str(integration_id),
            "volumes",
            resource_name
        )
        archive_path = os.path.join(
            whisper_path,
            "clusters",
            str(integration_id),
            "archive",
            "volumes"
        )
        if not os.path.exists(archive_path):
            os.makedirs(str(archive_path))
        resource_folder_name = str(resource_name) + "_" + \
            str(datetime.datetime.now().isoformat())
        archive_path = os.path.join(archive_path, resource_folder_name)
        if os.path.exists(resource_path):
            ret_val = os.system(
                "mv " + str(resource_path) + " " + str(archive_path)
            )
            if ret_val is 0:
                logger.log(
                    "info",
                    NS.get("publisher_id", None),
                    {
                        'message': "Volume " + str(resource_name) +
                        "deleted from graphite"
                    }
                )
            else:
                logger.log(
                    "error",
                    NS.get("publisher_id", None),
                    {
                        'message': "Volume " + str(resource_name) +
                        "deletion from graphite failed"
                    }
                )

    def delete_host_details(self, integration_id, resource_name, whisper_path):
        host_name = resource_name.replace(".", "_")
        volume_affected_list = []
        volume_key = os.path.join("clusters", str(integration_id), "Volumes")
        volume_list = create_dashboards.get_resource_keys("", volume_key)
        for volume_id in volume_list:
            flag = False
            single_volume_key = os.path.join(
                volume_key,
                volume_id,
                "Bricks"
            )
            subvolume_list = create_dashboards.get_resource_keys(
                "",
                single_volume_key
            )
            for subvolume in subvolume_list:
                subvolume_brick_key = os.path.join(
                    single_volume_key,
                    subvolume
                )
                brick_list = create_dashboards.get_resource_keys(
                    "",
                    subvolume_brick_key
                )
                if flag:
                    flag = False
                    break
                for brick in brick_list:
                    subvolume_hostname = brick.split(
                        ":", 1
                    )[0].replace(".", "_")
                    if host_name == subvolume_hostname:
                        volume_key = os.path.join(
                            volume_key,
                            volume_id,
                            "name"
                        )
                        try:
                            volume_name = etcd_utils.read(volume_key).value
                            volume_affected_list.append(volume_name)
                        except etcd.EtcdKeyNotFound:
                            pass
                        flag = True
                        break
        archive_path = os.path.join(
            whisper_path,
            "clusters",
            str(integration_id),
            "archive",
            "nodes"
        )
        if not os.path.exists(archive_path):
            os.makedirs(str(archive_path))
        resource_folder_name = str(host_name) + "_" + \
            str(datetime.datetime.now().isoformat())
        archive_path = os.path.join(archive_path, resource_folder_name)
        os.makedirs(str(archive_path))
        resource_path = os.path.join(
            whisper_path,
            "clusters",
            str(integration_id),
            "nodes",
            str(host_name)
        )
        if os.path.exists(resource_path):
            ret_val = os.system(
                "mv " + str(resource_path) + " " +
                str(archive_path)
            )
            if ret_val is 0:
                logger.log(
                    "info",
                    NS.get("publisher_id", None),
                    {
                        'message': "Host " + str(resource_name) +
                        "deleted from graphite"
                    }
                )
            else:
                logger.log(
                    "error",
                    NS.get("publisher_id", None),
                    {
                        'message': "Host " + str(resource_name) +
                        "deletion from graphite failed"
                    }
                )
        for vol_name in volume_affected_list:
            archive_path = os.path.join(
                archive_path,
                "volumes",
                vol_name
            )
            os.makedirs(str(archive_path))
            resource_path = os.path.join(
                whisper_path,
                "clusters",
                str(integration_id),
                "volumes",
                str(vol_name),
                "nodes",
                str(host_name)
            )
            if os.path.exists(resource_path):
                ret_val = os.system(
                    "mv " + str(resource_path) + " " +
                    str(archive_path)
                )
                if ret_val is 0:
                    logger.log(
                        "info",
                        NS.get("publisher_id", None),
                        {
                            'message': "Host " + str(resource_name) +
                            "deleted from graphite"
                        }
                    )
                else:
                    logger.log(
                        "error",
                        NS.get("publisher_id", None),
                        {
                            'message': "Host " + str(resource_name) +
                            "deletion from graphite failed"
                        }
                    )

    def update_graphite(self, integration_id, resource_name, resource_type):
        whisper_path = self.get_data_dir_path()
        if not whisper_path:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {'message': "Cannot retrieve whisper path"}
            )
            return
        if resource_type == "volume":
            self.delete_volume_details(
                integration_id,
                resource_name,
                whisper_path
            )
        if resource_type == "brick":
            self.delete_brick_details(
                integration_id,
                resource_name,
                whisper_path
            )
        if resource_type == "host":
            self.delete_host_details(
                integration_id,
                resource_name,
                whisper_path
            )
