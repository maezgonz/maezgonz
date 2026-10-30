import copy
import json
import os
import unittest

from scripts.gen_dashboard import validate_metrics


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METRICS_PATH = os.path.join(ROOT, "metrics.json")


class ValidateMetricsTests(unittest.TestCase):
    def load_valid_metrics(self):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_valid_metrics_pass_validation(self):
        metrics = self.load_valid_metrics()
        validate_metrics(metrics, METRICS_PATH)

    def test_invalid_gpu_cpu_format_raises(self):
        metrics = copy.deepcopy(self.load_valid_metrics())
        metrics["gpu_cpu"] = "310 / 867 / 135"

        with self.assertRaisesRegex(ValueError, "gpu_cpu"):
            validate_metrics(metrics, METRICS_PATH)

    def test_invalid_career_stages_raises(self):
        metrics = copy.deepcopy(self.load_valid_metrics())
        metrics["career_stages"] = [[1.2, "", "blue"]]

        with self.assertRaisesRegex(ValueError, "career_stages"):
            validate_metrics(metrics, METRICS_PATH)


if __name__ == "__main__":
    unittest.main()
