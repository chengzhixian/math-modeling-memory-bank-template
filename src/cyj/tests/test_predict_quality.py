import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/cyj"))
from predict_quality import predict_batch


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT / "outputs/cyj/interfaces/b7_example_request.json").read_text())

    def test_paired_output(self):
        result = predict_batch(self.payload)["results"]
        self.assertEqual([r["request_id"] for r in result], ["B7-line-362", "B7-line-363"])
        self.assertAlmostEqual(result[0]["loss_value"], 3.492870995028143)
        self.assertEqual(result[0]["uncertainty"]["sample_ids"], result[1]["uncertainty"]["sample_ids"])
        self.assertEqual(len(result[0]["uncertainty"]["conditional_mean_samples"]), 50)

    def test_invalid_batch_rejected(self):
        for field, value in (("request_id", "B7-line-362"), ("Q_score", "0.7"), ("mode", "formal"), ("Q_score", None)):
            payload = copy.deepcopy(self.payload)
            payload["requests"][1][field] = value
            with self.assertRaises(ValueError):
                predict_batch(payload)
        with self.assertRaises(ValueError):
            predict_batch({"expected_sha256": self.payload["expected_sha256"], "requests": []})

    def test_cli_from_other_directory(self):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "src/cyj/predict_quality.py"),
                              "--request", str(ROOT / "outputs/cyj/interfaces/b7_example_request.json")],
                             cwd=ROOT.parent, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["schema_version"], "cyj.b7_batch.v1")
