import socket

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import exceptions


def get_conf():
    try:
        # Graphite and Grafana will be running on localhost
        NS.config.data["grafana_host"] = "127.0.0.1"
        NS.config.data["grafana_port"] = 3000

        # Default values for graphite datasource
        NS.config.data["datasource_type"] = "graphite"
        NS.config.data["basicAuth"] = False

        # Grafana related configs
        NS.config.data["datasource"] = []
        NS.config.data["credentials"] = (
            NS.config.data["credentials"]["user"],
            NS.config.data["credentials"]["password"]
        )
    except exceptions.InvalidConfigurationException:
        err = exceptions.InvalidConfigurationException(
            "Error in loading configuration"
        )
        logger.log(
            "info",
            NS.get("publisher_id", None),
            {'message': str(err)}
        )
        raise err


def port_open(port, host='localhost'):
    """Check a given port is accessible

    :param port: (int) port number to check
    :param host: (str)hostname to check, default is localhost
    :return: (bool) true if the port is accessible
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect_ex((host, port))
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        return True
    except socket.error:
        return False


def fread(file_name):
    with open(file_name) as f:
        f_data = f.read()
    return f_data
