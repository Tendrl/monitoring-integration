from tendrl.commons import objects


class Trigger(objects.BaseObject):

    def __init__(self, action, resource_type, resource_name = None):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.action = action
