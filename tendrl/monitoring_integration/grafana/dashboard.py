import json
import traceback

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import dashboard_utils
from tendrl.monitoring_integration.grafana import datasource
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import utils


def upload_default_dashboards():
    dashboards = []
    NS.config.data["credentials"] = utils.get_credentials()
    try:
        main_org_id = grafana_org_utils.get_org_id(constants.MAIN_ORG)
        if main_org_id:
            response = grafana_org_utils.switch_context(
                json.loads(main_org_id)["id"]
            )
    except (exceptions.ConnectionFailedException, KeyError) as ex:
        msg = (json.loads(main_org_id)).get(
            "message", "Cannot connect to grafana")
        logger.log("error", NS.get("publisher_id", None),
                   {'message': msg})
        raise ex
    title = []
    # create datasource
    datasource.create()
    dashboards = dashboard_utils.get_all_dashboards()
    for dashboard_json in dashboards:
        title.append(dashboard_json["uri"].split('/')[1])

    for dashboard_json in NS.config.data["dashboards"]:
        if dashboard_json in title:
            msg = '\n' + "Dashboard " + str(dashboard_json) + \
                  " already exists" + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
            continue
        response = dashboard_utils.create_dashboard(dashboard_json)

        if response.status_code == 200:
            msg = '\n' + "Dashboard " + str(dashboard_json) + \
                  " uploaded successfully" + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        else:
            msg = ("Dashboard {0} upload failed. Error code: {1} ," +
                   "Error message: " + "{2} ").format(
                       str(dashboard_json),
                       str(response.status_code),
                       str(get_message_from_response(response)))
            logger.log("error", NS.get("publisher_id", None),
                       {'message': msg})
    try:
        dashboard_json = dashboard_utils.get_dashboard(
            NS.config.data["home_dashboard"])

        if 'dashboard' in dashboard_json:
            dashboard_id = dashboard_json.get('dashboard').get('id')
            response = dashboard_utils.set_home_dashboard(dashboard_id)

            response = dashboard_utils.set_home_dashboard(dashboard_id)
            if response.status_code == 200:
                msg = '\n' + "Dashboard " + \
                      str(NS.config.data["home_dashboard"]) + \
                      " is set as home dashboard" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
        else:
            msg = '\n' + str(dashboard_json.get('message')) + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
    except exceptions.ConnectionFailedException as ex:
        traceback.print_exc()
        logger.log("error", NS.get("publisher_id", None),
                   {'message': str(ex)})
        raise exceptions.ConnectionFailedException


def get_message_from_response(response_data):

    message = ""
    try:
        if isinstance(json.loads(response_data.content), list):
            message = str(json.loads(response_data.content)[0]["message"])
        else:
            message = str(json.loads(response_data.content)["message"])
    except (AttributeError, KeyError):
        pass

    return message
