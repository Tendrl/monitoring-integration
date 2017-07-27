import os
import socket
import sys


from ruamel import yaml


from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import config


def get_conf(file_name):

    try:
        yaml_config = _load_config(file_name)

        conf = config.Config()
        # Graphite and Grafana will be running on localhost
        conf.grafana_host = yaml_config.get('grafana_host', "localhost")
        conf.grafana_port = yaml_config.get('grafana_port', 3000)
        conf.datasource_host = yaml_config.get('datasource_host', "localhost")
        conf.datasource_port = yaml_config.get('datasource_port', 10080)

        # Datasource name in Grafana
        conf.datasource_name = yaml_config.get('datasource_name', "Graphite")

        # Default values for graphite datasource
        conf.datasource_type = yaml_config.get('datasource_type', "graphite")
        conf.basicAuth = yaml_config.get('basicAuth', False)

        # Datasource configs
        conf.access = yaml_config.get('access', "direct")
        conf.isDefault = yaml_config.get('isDefault', True)

        # Grafana related configs
        conf.dashboards = yaml_config.get('dashboards', [])
        conf.datasource = yaml_config.get('datasource', [])
        conf.auth = yaml_config.get('credentials', None)
        if conf.auth:
            conf.credentials = (conf.auth.get('user'),
                                conf.auth.get('password'))
        conf.home_dashboard = yaml_config.get('home_dashboard',
                                              'home_dashboard')
        conf.yaml = yaml_config
    except exceptions.InvalidConfigurationException:
        err = exceptions.InvalidConfigurationException(
            "Error in configuration %s" % (file_name)
        )
        sys.stderr.write(str(err))
        raise err

    return conf


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
        sys.stderr.write(str(err))
        raise err

    with open(yaml_cfg_file_path, 'r') as ymlfile:
        return yaml.safe_load(ymlfile)


def fread(file_name):
    with open(file_name) as f:
        f_data = f.read()
    return f_data
