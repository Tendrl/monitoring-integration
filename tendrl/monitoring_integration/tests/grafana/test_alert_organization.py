import etcd
from etcd import Client
import mock
from mock import patch

from tendrl.monitoring_integration.grafana import alert_organization
from tendrl.monitoring_integration.grafana import \
    datasource
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import \
    notification_channel
from tendrl.monitoring_integration.tests import test_init


@patch.object(etcd, "Client")
@patch.object(Client, "write")
@patch.object(grafana_org_utils, "switch_context")
@patch.object(datasource, "create")
@patch.object(notification_channel, "create_notification_channel")
def test_create(create_notification, create_ds, context, write, client):
    write.return_value = etcd.Client()
    client.return_value = etcd.Client()
    context.return_value = True
    create_ds.return_value = True
    create_notification.return_value = True
    test_init.init()
    with mock.patch("tendrl.commons.utils.log_utils.log"):
        with patch.object(grafana_org_utils, "get_org_id") as org_utils:
            org_utils.return_value = '{"id": 2}'
            with patch.object(grafana_org_utils, "get_auth_keys") as auth_key:
                auth_key.return_value = [
                    {
                        "name": "grafana_auth_key",
                        "role": "Admin"
                    }
                ]
                with patch.object(NS.monitoring.objects.AlertOrganization,
                                  "load") as load:
                    obj = NS.monitoring.objects.AlertOrganization(
                        auth_key="grafana_key")
                    load.return_value = obj
                    alert_organization.create()
                    if not NS.config.data["org_id"] == 2:
                        raise AssertionError()
                    if not NS.config.data["grafana_auth_key"] == \
                            "grafana_key":
                        raise AssertionError()
        with patch.object(grafana_org_utils, "get_org_id") as org_utils:
            org_utils.return_value = '{"message": "Organization not found"}'
            with patch.object(grafana_org_utils, "create_org") as create_org:
                create_org.return_value = 3
                with patch.object(grafana_org_utils,
                                  "get_auth_keys") as auth_key:
                    auth_key.return_value = []
                    with patch.object(grafana_org_utils,
                                      "create_api_token") as api_token:
                        api_token.return_value = "grafana_key_new"
                        alert_organization.create()
                        if not NS.config.data["org_id"] == 3:
                            raise AssertionError()
                        if not NS.config.data["grafana_auth_key"] ==  \
                                "grafana_key_new":
                            raise AssertionError()
        with patch.object(grafana_org_utils, "get_org_id") as org_utils:
            org_utils.return_value = '{}'
            with patch.object(grafana_org_utils, "get_auth_keys") as auth_key:
                auth_key.return_value = {}
                alert_organization.create()
                if not NS.config.data["org_id"] is None:
                    raise AssertionError()
                if not NS.config.data["grafana_auth_key"] is None:
                    raise AssertionError()
        with patch.object(grafana_org_utils, "get_org_id") as org_utils:
            org_utils.return_value = {}
