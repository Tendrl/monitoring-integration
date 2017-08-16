import __builtin__
import os
import socket


from ruamel import yaml


from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import config
from tendrl.commons.utils import log_utils as logger


def get_conf():

    try:

        # Graphite and Grafana will be running on localhost
        NS.config.data["grafana_host"] = "localhost"
        NS.config.data["grafana_port"] = 3000
        NS.config.data["datasource_port"] = 10080

        # Default values for graphite datasource
        NS.config.data["datasource_type"] = "graphite"
        NS.config.data["basicAuth"] = False

        # Grafana related configs
        NS.config.data["datasource"] = []
        NS.config.data["credentials"] = (NS.config.data["credentials"]["user"],
                                         NS.config.data["credentials"]["password"])

    except exceptions.InvalidConfigurationException:
        err = exceptions.InvalidConfigurationException(
            "Error in configuration %s" % (file_name)
        )
        logger.log("info", NS.get("publisher_id", None),
                   {'message': str(err)})

        raise err


def port_open(port, host='localhost'):
    """
    Check a given port is accessible
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


def _load_config(yaml_cfg_file_path):

    if not os.path.exists(yaml_cfg_file_path):
        err = exceptions.ConfigNotFoundException(
            "Configuration not found at %s" %
            (yaml_cfg_file_path)
        )
        logger.log("info", NS.get("publisher_id", None),
                   {'message': str(err)})
        raise err

    with open(yaml_cfg_file_path, 'r') as ymlfile:
        return yaml.safe_load(ymlfile)


def fread(file_name):
    with open(file_name) as f:
        f_data = f.read()
    return f_data
