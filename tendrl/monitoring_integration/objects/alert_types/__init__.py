from tendrl.commons import objects


class AlertTypes(objects.BaseObject):
    def __init__(self, types=None, *args, **kwargs):
        super(AlertTypes, self).__init__(*args, **kwargs)
        self.types = types
        self.value = 'alerting/alert_types'
