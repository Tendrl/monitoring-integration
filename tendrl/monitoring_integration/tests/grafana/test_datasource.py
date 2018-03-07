import maps
import mock

from tendrl.monitoring_integration.grafana import datasource
from tendrl.monitoring_integration.grafana import datasource_utils
from tendrl.monitoring_integration.tests import test_init


def pass_create_datasource():
    response = maps.NamedDict(status_code=200, content="{}")
    return response


def update_create_datasource():
    response = maps.NamedDict(
        status_code=404,
        content='{"message": "Data source with same name already exists"}'
    )
    return response


def get_data_source():
    response = maps.NamedDict(status_code=200, content='{"id": 1}')
    return response


def get_data_source_fail():
    response = maps.NamedDict(status_code=404, content='{}')
    return response


def update(ds_id):
    response = maps.NamedDict(status_code=200, content="{}")
    return response


def fail_update(ds_id):
    response = maps.NamedDict(status_code=404, content="{}")
    return response


def test_create():
    with mock.patch("tendrl.commons.utils.log_utils.log") as mock_log:
        test_init.init()
        with mock.patch.object(
            datasource_utils, "create_datasource", pass_create_datasource
        ):
            datasource.create()
            mock_log.assert_called_with(
                'info',
                'monitoring_integration',
                {'message': 'Datasource created successfully'}
            )
        with mock.patch.object(
            datasource_utils, "create_datasource", update_create_datasource
        ):
            with mock.patch.object(
                datasource_utils, "get_data_source", get_data_source_fail
            ):
                datasource.create()
                mock_log.assert_called_with(
                    'error',
                    'monitoring_integration',
                    {'message': 'Unable to find datasource id'}
                )
            with mock.patch.object(
                datasource_utils, "get_data_source", get_data_source
            ):
                with mock.patch.object(
                    datasource_utils, "update_datasource", update
                ):
                    datasource.create()
                    mock_log.assert_called_with(
                        'info',
                        'monitoring_integration',
                        {'message': 'Datasource is updated successfully'}
                    )
                with mock.patch.object(
                    datasource_utils, "update_datasource", fail_update
                ):
                    datasource.create()
                    mock_log.assert_called_with(
                        'error',
                        'monitoring_integration',
                        {'message': 'Unable to update datasource'}
                    )
