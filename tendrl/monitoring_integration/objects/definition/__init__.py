import pkg_resources
from ruamel import yaml

from tendrl.commons import objects


class Definition(objects.BaseObject):
    internal = True

    def __init__(self, *args, **kwargs):
        self._defs = {}
        super(Definition, self).__init__(*args, **kwargs)

        self.data = pkg_resources.resource_string(
            __name__,
            "monitoring_integration.yaml"
        )
        self._parsed_defs = yaml.safe_load(self.data)
        self.value = "_NS/monitoring/definitions"

    def get_parsed_defs(self):
        if self._parsed_defs:
            return self._parsed_defs
        self._parsed_defs = yaml.safe_load(self.data)
        return self._parsed_defs
