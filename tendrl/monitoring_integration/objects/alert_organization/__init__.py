from tendrl.commons import objects


class AlertOrganization(objects.BaseObject):
    def __init__(self, org_name=None, org_id=None,
                 auth_key=None, *args, **kwargs):
        super(AlertOrganization, self).__init__(*args, **kwargs)
        self.org_name = org_name
        self.org_id = org_id
        self.auth_key = auth_key
        self.value = '_NS/monitoring/alert_organization'

    def render(self):
        return super(AlertOrganization, self).render()
