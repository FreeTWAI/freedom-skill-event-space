import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts" / "validate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PlanValidation(unittest.TestCase):
    def sample(self):
        return json.loads((ROOT / "examples" / "event-plan.json").read_text(encoding="utf-8"))

    def test_synthetic_example_is_valid(self):
        self.assertEqual(module.validate(self.sample()), [])

    def test_all_shipped_json_plans_are_valid(self):
        for directory in ("templates", "examples"):
            paths = sorted((ROOT / directory).rglob("*.json"))
            self.assertTrue(paths, directory + " must contain JSON plans")
            for path in paths:
                with self.subTest(path=str(path.relative_to(ROOT))):
                    data = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(module.validate(data), [])

    def test_domain_constraint_is_enforced(self):
        bad = self.sample()
        bad['expected_attendees'] = bad['venue_capacity'] + 1
        self.assertTrue(module.validate(bad))

    def test_conflicting_work_plan_is_rejected(self):
        bad = self.sample()
        bad['agenda'][1]['start_minute'] = 1
        self.assertTrue(module.validate(bad))

    def test_private_record_is_not_a_public_example(self):
        bad = self.sample()
        bad['data_classification'] = 'private'
        self.assertTrue(module.validate(bad))

    def test_non_object_is_rejected(self):
        self.assertTrue(module.validate([]))

    def test_missing_or_invalid_title(self):
        bad = self.sample()
        del bad['title']
        errors = module.validate(bad)
        self.assertIn("title is required", errors)

        bad['title'] = ""
        errors = module.validate(bad)
        self.assertIn("title is required", errors)

        bad['title'] = "   "
        errors = module.validate(bad)
        self.assertIn("title is required", errors)

        bad['title'] = 123
        errors = module.validate(bad)
        self.assertIn("title is required", errors)

    def test_invalid_kind(self):
        bad = self.sample()
        bad['kind'] = 'wrong-kind'
        errors = module.validate(bad)
        self.assertIn("kind must be event-space", errors)

    def test_records_function_errors(self):
        bad = self.sample()
        bad['agenda'] = "not a list"
        errors = module.validate(bad)
        self.assertIn("agenda must contain at least one object", errors)

        bad['agenda'] = []
        errors = module.validate(bad)
        self.assertIn("agenda must contain at least one object", errors)

        bad['agenda'] = [{"valid": "item"}, "not a dict"]
        errors = module.validate(bad)
        self.assertIn("agenda must contain at least one object", errors)

    def test_agenda_title_is_required(self):
        bad = self.sample()
        del bad['agenda'][0]['title']
        errors = module.validate(bad)
        self.assertIn("agenda title is required", errors)

        bad['agenda'][0]['title'] = "   "
        errors = module.validate(bad)
        self.assertIn("agenda title is required", errors)

    def test_unique_ids(self):
        errors = []

        # Valid ids
        items_valid = [{"id": "a"}, {"id": "b"}]
        ids = module.unique_ids(items_valid, "test", errors)
        self.assertEqual(ids, {"a", "b"})
        self.assertEqual(errors, [])

        # Invalid id types/empty
        items_invalid = [{"id": "a"}, {"id": ""}, {"id": 123}]
        ids = module.unique_ids(items_invalid, "test", errors)
        self.assertEqual(ids, set())
        self.assertIn("test ids must be nonempty strings", errors)

        # Duplicate ids
        errors = []
        items_duplicate = [{"id": "a"}, {"id": "a"}]
        ids = module.unique_ids(items_duplicate, "test", errors)
        self.assertEqual(ids, {"a"})
        self.assertIn("test ids must be unique", errors)
