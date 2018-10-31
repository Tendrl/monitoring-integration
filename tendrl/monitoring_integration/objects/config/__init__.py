from tendrl.commons import config as cmn_config
from tendrl.commons import objects


class Config(objects.BaseObject):
    internal = True

    def __init__(self, config=None, *args, **kwargs):
        self._defs = {}
        super(Config, self).__init__(*args, **kwargs)

        self.data = config or cmn_config.load_config(
            'monitoring-integration',
            "/etc/tendrl/monitoring-integration/"
            "monitoring-integration.conf.yaml"
        )
        self.value = "_NS/monitoring/config"
