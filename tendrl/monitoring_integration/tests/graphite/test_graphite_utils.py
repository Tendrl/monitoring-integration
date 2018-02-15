import json
from mock import patch
import os

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.graphite import graphite_utils


def test_graphite_utils():
    path = os.path.join(os.path.dirname(__file__),
                        "objects.json")
    objects = json.load(open(path))
    path = os.path.join(os.path.dirname(__file__),
                        "cluster_details.json")
    cluster_details = json.load(open(path))
    with patch.object(logger, "log"):
        path = os.path.join(os.path.dirname(__file__),
                            "result.json")
        result = json.load(open(path))
        metrics = graphite_utils.create_metrics(
            objects, cluster_details
        )
        for metric in metrics:
            if metric not in result:
                raise AssertionError()
