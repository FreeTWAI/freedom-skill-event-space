import importlib.util
import json
import timeit
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts" / "validate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PerformanceBenchmark(unittest.TestCase):
    def test_validation_latency(self):
        sample = json.loads((ROOT / "examples" / "event-plan.json").read_text(encoding="utf-8"))

        # Create a large payload to test performance at scale
        large_sample = sample.copy()
        large_sample["agenda"] = []
        for i in range(100):
            for item in sample["agenda"]:
                new_item = item.copy()
                new_item["start_minute"] = item["start_minute"] + i * 1000
                large_sample["agenda"].append(new_item)

        def run_validation():
            module.validate(large_sample)

        # Warm-up
        run_validation()

        # Measure latency
        number_of_runs = 1000
        latency = timeit.timeit(run_validation, number=number_of_runs)
        avg_latency = latency / number_of_runs

        print(f"\nAverage validation latency for large agenda (300 items): {avg_latency * 1000:.3f} ms")

        # Expect the validation to take less than 5ms on average for 300 items
        self.assertLess(avg_latency, 0.005, "Validation latency exceeds the 5ms threshold")


if __name__ == "__main__":
    unittest.main()
