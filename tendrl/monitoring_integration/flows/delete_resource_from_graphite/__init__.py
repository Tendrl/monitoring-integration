from tendrl.commons import flows
from tendrl.monitoring_integration.flows.delete_resource_from_graphite import \
    graphite_delete_utils


class DeleteResourceFromGraphite(flows.BaseFlow):

    def run(self):
        super(DeleteResourceFromGraphite, self).run()
        integration_id = self.parameters.get("TendrlContext.integration_id")
        resource_name = str(self.parameters.get("Trigger.resource_name"))
        resource_type = str(self.parameters.get(
            "Trigger.resource_type")).lower()
        graphite_delete_utils.update_graphite(
            integration_id, resource_name, resource_type
        )
