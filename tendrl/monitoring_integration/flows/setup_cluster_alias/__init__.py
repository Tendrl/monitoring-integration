import os

from tendrl.commons import flows
from tendrl.commons.flows.exceptions import FlowExecutionFailedError
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.graphite import graphite_utils


class SetupClusterAlias(flows.BaseFlow):

    def run(self):
        super(SetupClusterAlias, self).run()
        integration_id = self.parameters["TendrlContext.integration_id"]
        short_name = self.parameters.get("Cluster.short_name")
        alias_dir_path = "%snames" % graphite_utils.get_data_dir_path()
        if not os.path.exists(alias_dir_path):
            try:
                os.makedirs(str(alias_dir_path))
            except OSError as ex:
                raise FlowExecutionFailedError(
                    "Failed to create cluster alias dir: (%s)"
                    " .Error: (%s)" %
                    (str(alias_dir_path), ex)
                )
        if short_name in [None, ""]:
            short_name = integration_id
        os.symlink(
            "%s/clusters/%s" % (
                graphite_utils.get_data_dir_path(),
                integration_id
            ),
            "%s/%s" % (alias_dir_path, short_name)
        )
        # Assign permission for carbon user
        try:
            storage_dir_path = graphite_utils.get_graphite_path(
                "cache", "storage_dir"
            )
            graphite_utils.change_owner(
                storage_dir_path,
                "carbon",
                "carbon",
                recursive=True
            )
        except (KeyError, OSError, TypeError) as ex:
            raise FlowExecutionFailedError(
                "Unable to modify the ownership of %s" % storage_dir_path
            )
        logger.log(
            "debug",
            NS.publisher_id,
            {
                "message": "Link %s -> %s created" %
                (
                    "%s/%s" % (alias_dir_path, short_name),
                    "%s/clusters/%s" % (
                        graphite_utils.get_data_dir_path(),
                        integration_id
                    )
                )
            },
            job_id=self.parameters['job_id'],
            flow_id=self.parameters['flow_id']
        )
        return True
