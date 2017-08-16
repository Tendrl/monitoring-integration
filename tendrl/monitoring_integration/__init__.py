try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()


from tendrl.commons import TendrlNS


class MonitoringIntegrationNS(TendrlNS):

    def __init__(self, ns_name="monitoring",
                 ns_src="tendrl.monitoring_integration"):
        super(MonitoringIntegrationNS, self).__init__(ns_name, ns_src)
