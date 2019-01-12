#!/usr/bin/python

import argparse
import ConfigParser
import requests

from requests.auth import HTTPBasicAuth
from tendrl.monitoring_integration.upgrades import utils


def delete_dashboards(server_ip, user, password):

    dashboards = ["cluster-dashboard", "brick-dashboard", "host-dashboard",
                  "volume-dashboard"]

    headers = {'content-type': 'application/json'}

    for dashboard in dashboards:
        url = "http://%s/grafana/api/dashboards/db/%s" % (server_ip, dashboard)
        utils.print_message(url)
        response = requests.delete(url, headers=headers,
                                   auth=HTTPBasicAuth(user, password))
        if response.status_code == 200:
            utils.print_message("Deleted %s" % dashboard)
        else:
            utils.print_message(
                "Failed to delete %s %s" % (dashboard, response.json())
            )

    # Deleting the alerts dashboards
    url = "http://%s/grafana/api/orgs/name/Alert_dashboard" \
          % server_ip
    utils.print_message("Getting alerts organization id\n %s" % url)
    response = requests.get(url, headers=headers,
                            auth=HTTPBasicAuth(user, password))
    resp = response.json()

    if 'id' in resp:
        id = resp['id']
        url = "http://%s/grafana/api/orgs/%s" % (server_ip, id)
        utils.print_message("Deleting alerts organization\n %s" % url)
        response = requests.delete(url, headers=headers,
                                   auth=HTTPBasicAuth(user, password))
        resp = response.json()
        if resp == {u'message': u'Organization deleted'}:
            utils.print_message("Deleted Alert dashboards")
        else:
            utils.print_message(
                "Failed to delete Alert dashboards %s" % resp
            )

    else:
        utils.print_message(
            "Failed to delete Alert dashboards."
            "Organization id not found %s" % resp
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="grafana admin_user username")
    parser.add_argument("--password", help="grafana admin_user password")
    args = parser.parse_args()
    try:
        utils.print_message("Stopping carbon-cache service")
        utils.stop_service("carbon-cache")
        utils.print_message("Stopping httpd service")
        utils.stop_service("httpd")
        utils.print_message("Modifying brick path separator")
        # Modifying brick path separator from | to :
        utils.command_exec(
            "find /var/lib/carbon/whisper/tendrl/ -depth  "
            "-type d -name '*|*' -execdir bash -c "
            "'mv \"$1\" \"${1//|/:}\"' bash {} ';'"
        )
        utils.print_message("Removing graphite DB")
        utils.remove_file("/var/lib/graphite-web/graphite.db")
        utils.print_message("Initializing graphite DB")
        utils.command_exec(
            "django-admin migrate "
            "--settings=graphite.settings "
            "--run-syncdb"
        )
        utils.print_message("Starting httpd service")
        utils.start_service("httpd")
        # getting grafana admin_username and password
        config = ConfigParser.ConfigParser()
        config.read('/etc/tendrl/monitoring-integration/grafana/grafana.ini')
        username = config.get('security', 'admin_user')
        password = config.get('security', 'admin_password')
        default_ip = "127.0.0.1"

        if args.username:
            username = args.username
        if args.password:
            password = args.password

        utils.print_message("Clearing grafana dashboards")
        delete_dashboards(server_ip=default_ip, user=username,
                          password=password)
        utils.print_message(
            "Complete -- Please start tendrl-monitoring-integration "
            "service"
        )

    except Exception as e:
        utils.print_message(
            "Failed in deleting dashboards with error: %s" % e
        )


if __name__ == '__main__':
    main()
