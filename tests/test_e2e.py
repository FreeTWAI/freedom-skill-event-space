import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts" / "validate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class E2EValidation(unittest.TestCase):
    def get_valid_plan(self):
        return {
            "kind": "event-space",
            "title": "E2E Test Plan",
            "expected_attendees": 10,
            "venue_capacity": 20,
            "roles": ["Host", "Helper"],
            "agenda": [
                {
                    "start_minute": 0,
                    "duration_minutes": 30,
                    "title": "Welcome",
                    "owner_role": "Host"
                },
                {
                    "start_minute": 30,
                    "duration_minutes": 60,
                    "title": "Main Event",
                    "owner_role": "Host"
                }
            ],
            "data_classification": "synthetic"
        }

    def test_ingestion_valid_plan(self):
        plan = self.get_valid_plan()
        errors = module.validate(plan)
        self.assertEqual(errors, [])

    def test_capacity_exceeded(self):
        plan = self.get_valid_plan()
        plan["expected_attendees"] = 25
        plan["venue_capacity"] = 20
        errors = module.validate(plan)
        self.assertIn("attendance exceeds the stated venue capacity", errors)

    def test_invalid_capacity_types(self):
        plan = self.get_valid_plan()
        plan["expected_attendees"] = "10"
        plan["venue_capacity"] = "20"
        errors = module.validate(plan)
        self.assertIn("attendance and capacity must be positive integers", errors)

    def test_agenda_overlap(self):
        plan = self.get_valid_plan()
        plan["agenda"][1]["start_minute"] = 15
        errors = module.validate(plan)
        self.assertIn("agenda entries overlap or are out of order", errors)

    def test_agenda_out_of_order(self):
        plan = self.get_valid_plan()
        plan["agenda"].reverse()
        errors = module.validate(plan)
        self.assertIn("agenda entries overlap or are out of order", errors)

    def test_agenda_invalid_timing(self):
        plan = self.get_valid_plan()
        plan["agenda"][0]["start_minute"] = -1
        errors = module.validate(plan)
        self.assertIn("agenda timing must be nonnegative with a positive duration", errors)

    def test_role_checklist(self):
        plan = self.get_valid_plan()
        plan["agenda"][0]["owner_role"] = "Nonexistent Role"
        errors = module.validate(plan)
        self.assertIn("each agenda item needs a listed owner role", errors)

    def test_missing_roles_list(self):
        plan = self.get_valid_plan()
        plan["roles"] = "not a list"
        errors = module.validate(plan)
        self.assertIn("roles must be a list of nonempty names", errors)
        self.assertIn("each agenda item needs a listed owner role", errors)

    def test_space_capacity_exact_match(self):
        plan = self.get_valid_plan()
        plan["expected_attendees"] = 20
        plan["venue_capacity"] = 20
        errors = module.validate(plan)
        self.assertEqual(errors, [])

    def test_equipment_checklist_parsing(self):
        plan = self.get_valid_plan()
        plan["equipment_checklist"] = ["Projector", "Microphone", "Whiteboard"]
        errors = module.validate(plan)
        self.assertEqual(errors, [])

    def test_event_flow_diagrams(self):
        plan = self.get_valid_plan()
        plan["flow_diagrams"] = ["entrance.png", "stage_layout.png"]
        errors = module.validate(plan)
        self.assertEqual(errors, [])
