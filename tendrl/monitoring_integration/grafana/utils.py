import etcd
import socket


from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger


def get_credentials():
    credentials = (
        NS.config.data["credentials"]["user"],
        NS.config.data["credentials"]["password"]
    )
    return credentials


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


def get_resource_keys(key, resource_name):
    resource_list = []
    try:
        resource_details = etcd_utils.read(key + "/" + str(resource_name))
        for resource in resource_details.leaves:
            resource_list.append(resource.key.split('/')[-1])
    except (KeyError, etcd.EtcdKeyNotFound) as ex:
        logger.log(
            "debug",
            NS.get("publisher_id", None),
            {
                'message': "Error while fetching " + str(
                    resource_name).split('/')[0] + str(ex)
            }
        )
    return resource_list
