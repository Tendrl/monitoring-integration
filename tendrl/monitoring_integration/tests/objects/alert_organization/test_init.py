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
        },
        {
            'key': '/_NS/monitoring/alert_organization/hash',
            'value': 'dbe23ea17c68ff20e8b8b678997531a4',
            'name': 'hash',
            'dir': False
        }
    ]
    for atrr in obj.render():
        if atrr not in result:
            raise AssertionError()
