from tendrl.monitoring_integration.objects import alert_organization


def test_alert_organization():
    obj = alert_organization.AlertOrganization()
    result = [
        {
            'name': 'auth_key',
            'key': '/_NS/monitoring/alert_organization/auth_key',
            'value': '',
            'dir': False
        },
        {
            'name': 'org_id',
            'key': '/_NS/monitoring/alert_organization/org_id',
            'value': '',
            'dir': False
        },
        {
            'name': 'org_name',
            'key': '/_NS/monitoring/alert_organization/org_name',
            'value': '',
            'dir': False
        }
    ]
    for attr in obj.render():
        if "hash" not in attr['key']and attr not in result:
            raise AssertionError()
