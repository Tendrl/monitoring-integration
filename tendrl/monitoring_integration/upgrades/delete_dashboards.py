#!/usr/bin/python

import argparse
import ConfigParser
import os
import requests

from requests.auth import HTTPBasicAuth


def delete_dashboards(server_ip, user, password):

    dashboards = ["cluster-dashboard", "brick-dashboard", "host-dashboard",
                  "volume-dashboard"]

    headers = {'content-type': 'application/json'}

    for dashboard in dashboards:
        url = "http://%s/grafana/api/dashboards/db/%s" % (server_ip, dashboard)
        print (url)
        response = requests.delete(url, headers=headers,
                                   auth=HTTPBasicAuth(user, password))
        if response.status_code == 200:
            print ("Deleted %s \n" % dashboard)
        else:
            print ("Failed to delete %s %s \n" % (dashboard, response.json()))

    # Deleting the alerts dashboards
    url = "http://%s/grafana/api/orgs/name/Alert_dashboard" \
          % server_ip
    print ("Getting alerts organization id\n %s \n" % url)
    response = requests.get(url, headers=headers,
                            auth=HTTPBasicAuth(user, password))
    resp = response.json()

    if 'id' in resp:
        id = resp['id']
        url = "http://%s/grafana/api/orgs/%s" % (server_ip, id)
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
    try:
        print ("\n Migrating graphite data \n")
        os.system(
            "PYTHONPATH=$GRAPHITE_ROOT/webapp/ "
            "django-admin migrate --fake dashboard "
            "--settings=graphite.settings "
            "--run-syncdb"
        )
        os.system(
            "PYTHONPATH=$GRAPHITE_ROOT/webapp/ "
            "django-admin migrate --fake-initial "
            "--settings=graphite.settings "
            "--run-syncdb"
        )
        parser = argparse.ArgumentParser()
        parser.add_argument("--username", help="grafana admin_user username")
        parser.add_argument("--password", help="grafana admin_user password")

        # getting grafana admin_username and password
        config = ConfigParser.ConfigParser()
        config.read('/etc/tendrl/monitoring-integration/grafana/grafana.ini')
        username = config.get('security', 'admin_user')
        password = config.get('security', 'admin_password')
        default_ip = "127.0.0.1"

        args = parser.parse_args()
        if args.username:
            username = args.username
        if args.password:
            password = args.password

        print ("\n Clearing grafana dashboards \n")
        delete_dashboards(server_ip=default_ip, user=username,
                          password=password)
        print ("\n Complete -- Please start tendrl-monitoring-integration "
               "service")

    except Exception as e:
        print ("Failed in deleting dashboards with error: %s" % e)


if __name__ == '__main__':
    main()
