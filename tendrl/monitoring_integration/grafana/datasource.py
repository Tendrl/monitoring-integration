import json

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import datasource_utils

DATA_SOURCE_TYPE = "graphite"


def create():
    # No basic auth
    NS.config.data["basicAuth"] = False
    # For now we are supporting only graphite
    # Move this to config file when we support multiple
    # type of data_source
    NS.config.data["datasource_type"] = DATA_SOURCE_TYPE
    # Check data source is already exist
    response = datasource_utils.create_datasource()
    result = json.loads(response.content)
    if response.status_code == 200:
        msg = "Datasource created successfully"
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})
    elif "message" in result and result["message"] == \
            "Data source with same name already exists":
        # update datasource
        resp = datasource_utils.get_data_source()
        if resp.status_code == 200:
            result = json.loads(resp.content)
            resp = datasource_utils.update_datasource(result["id"])
            if resp.status_code == 200:
                msg = "Datasource is updated successfully"
                logger.log("debug", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = "Unable to update datasource"
                logger.log("debug", NS.get("publisher_id", None),
                           {'message': msg})
        else:
            msg = "Unable to find datasource id"
            logger.log("debug", NS.get("publisher_id", None),
                       {'message': msg})
