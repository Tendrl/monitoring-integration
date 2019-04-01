#!/usr/bin/python

import argparse
import ConfigParser
import requests

from requests.auth import HTTPBasicAuth
from tendrl.monitoring_integration.graphite import graphite_utils
from tendrl.monitoring_integration.upgrades import utils


def delete_dashboards(server_ip, port, user, password):

    dashboards = ["cluster-dashboard", "brick-dashboard", "host-dashboard",
                  "volume-dashboard"]

    headers = {'content-type': 'application/json'}

    for dashboard in dashboards:
        url = "http://%s:%s/api/dashboards/db/%s" % (
            server_ip, port, dashboard
        )
        print (url)
        response = requests.delete(url, headers=headers,
                                   auth=HTTPBasicAuth(user, password))
        if response.status_code == 200:
            print ("Deleted %s \n" % dashboard)
        else:
            print ("Failed to delete %s %s \n" % (dashboard, response.json()))

    # Deleting the alerts dashboards
    url = "http://%s:%s/api/orgs/name/Alert_dashboard" \
          % (server_ip, port)
    print ("Getting alerts organization id\n %s \n" % url)
    response = requests.get(url, headers=headers,
                            auth=HTTPBasicAuth(user, password))
    resp = response.json()

    if 'id' in resp:
        id = resp['id']
        url = "http://%s:%s/api/orgs/%s" % (server_ip, port, id)
        print ("Deleting alerts organization\n %s" % url)
        response = requests.delete(url, headers=headers,
                                   auth=HTTPBasicAuth(user, password))
        resp = response.json()
        if resp == {u'message': u'Organization deleted'}:
            print ("Deleted Alert dashboards")
        else:
            print ("Failed to delete Alert dashboards %s" % resp)

    else:
        print ("Failed to delete Alert dashboards.")
        print ("Organization id not found %s" % resp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="grafana admin_user username")
    parser.add_argument("--password", help="grafana admin_user password")
    args = parser.parse_args()

    try:
        print ("\n Stopping carbon-cache service \n")
        utils.stop_service("carbon-cache")
        print ("\n Stopping httpd service \n")
        utils.stop_service("httpd")
        print ("\n Modifying brick path separator \n")
        # Modifying brick path separator | to :
        utils.command_exec(
            "find /var/lib/carbon/whisper/tendrl/ -depth  "
            "-type d -name '*|*' -execdir bash -c "
            "'mv \"$1\" \"${1//|/:}\"' bash {} ';'"
        )
        print ("\n Removing graphite DB \n")
        utils.remove_file("/var/lib/graphite-web/graphite.db")
        print ("\n Initializing graphite DB \n")
        utils.command_exec(
            "django-admin migrate "
            "--settings=graphite.settings "
            "--run-syncdb"
        )
        print ("\n Allow apache to access graphite.db file \n")
        graphite_utils.change_owner(
            "/var/lib/graphite-web/graphite.db",
            "apache",
            "apache"
        )
        print ("\n Allow apache to log messages in graphite-web \n")
        graphite_utils.change_owner(
            "/var/log/graphite-web",
            "apache",
            "apache",
            True
        )
        print ("\n Starting carbon-cache service \n")
        utils.start_service("carbon-cache")
        print ("\n Starting httpd service \n")
        utils.start_service("httpd")
        # getting grafana admin_username and password
        config = ConfigParser.ConfigParser()
        config.read('/etc/tendrl/monitoring-integration/grafana/grafana.ini')
        username = config.get('security', 'admin_user')
        password = config.get('security', 'admin_password')
        default_ip = "127.0.0.1"
        default_port = 3000
        if args.username:
            username = args.username
        if args.password:
            password = args.password

        print ("\n Clearing grafana dashboards \n")
        delete_dashboards(
            server_ip=default_ip,
            port=default_port,
            user=username,
            password=password
        )
        print ("\n Complete -- Please start tendrl-monitoring-integration "
               "service")

    except Exception as e:
        print ("Failed in deleting dashboards with error: %s" % e)


if __name__ == '__main__':
    main()
