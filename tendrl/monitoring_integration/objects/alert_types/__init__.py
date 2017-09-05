from tendrl.commons import objects


class AlertTypes(objects.BaseObject):
    def __init__(self, classification=None, types=None, *args, **kwargs):
        super(AlertTypes, self).__init__(*args, **kwargs)
        self.classification = classification
        self.types = types
        self.value = 'alerting/alert_types/{0}'

    def render(self):
        self.value = self.value.format(
            self.classification
        )
        return super(AlertTypes, self).render()
