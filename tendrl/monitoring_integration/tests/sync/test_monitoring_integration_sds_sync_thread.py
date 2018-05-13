import __builtin__
import etcd
import json
from mock import MagicMock
from mock import Mock
from mock import patch
import pytest
from tendrl.monitoring_integration.sync import \
    MonitoringIntegrationSdsSyncThread


class TestMonitoringIntegrationSdsSyncThread(object):
    def __init_monitoring_integration_sds_sync_thread(self):
        self._complete = MagicMock()
        self._complete.is_set.side_effect = [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            True
        ]
        self.plugin_obj = MagicMock()
        self.sync_interval = None

    @classmethod
    @patch.object(
        MonitoringIntegrationSdsSyncThread,
        '__init__',
        __init_monitoring_integration_sds_sync_thread
    )
    def setup_class(cls):
        cls.__sync_thread = MonitoringIntegrationSdsSyncThread()

    @patch('tendrl.commons.utils.etcd_utils.read')
    @patch.object(__builtin__, 'NS', create=True)
    @patch('time.sleep', Mock())
    def test_error_on_invalid_sync_interval_config(self, NS, etcd_read):
        with pytest.raises(ValueError):
            NS.monitoring.definitions.get_parsed_defs.return_value = {
                'namespace.monitoring': {'graphite_data': None}
            }

            json_valid_config_data_bad_sync_interval = Mock()
            json_valid_config_data_bad_sync_interval.value =\
                self.__etcd_read_json_valid_config_data('')
            etcd_read.side_effect = [
                etcd.EtcdKeyNotFound(),
                json_valid_config_data_bad_sync_interval,
            ]

            self.__sync_thread.run()

    @patch('tendrl.commons.utils.etcd_utils.read')
    @patch(
        'tendrl.monitoring_integration.graphite.graphite_utils.'
        'create_cluster_alias'
    )
    @patch(
        'tendrl.monitoring_integration.graphite.graphite_utils.'
        'create_metrics'
    )
    @patch.object(__builtin__, 'NS', create=True)
    @patch('time.sleep', Mock())
    def test_run_unit_complete(
            self,
            NS,
            create_metrics,
            create_cluster_alias,
            etcd_read
    ):
        NS.monitoring.definitions.get_parsed_defs.return_value = {
            'namespace.monitoring': {'graphite_data': None}
        }

        json_valid_config_data = Mock()
        json_valid_config_data.value =\
            self.__etcd_read_json_valid_config_data()
        etcd_read.side_effect = [
            etcd.EtcdKeyNotFound(),
            json_valid_config_data,
        ]

        create_cluster_alias.return_value = None

        metric = {'key1': 'value1', 'key2': None}
        create_metrics.side_effect = [
            etcd.EtcdKeyNotFound(),
            [metric],
            [metric],
            [metric],
            [metric],
            [metric],
            [metric]
        ]

        self.__sync_thread.run()

    def test_stop(self):
        self.__sync_thread.stop()

    @staticmethod
    def __etcd_read_json_valid_config_data(sync_interval=0):
        return json.dumps({'data': {'sync_interval': sync_interval}})
