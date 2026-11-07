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


import subprocess
import tempfile
import sys
import os

class CLIIntegration(unittest.TestCase):
    def setUp(self):
        self.script_path = ROOT / "scripts" / "validate.py"
        self.valid_plan = {
            "kind": "event-space",
            "title": "CLI Test Plan",
            "expected_attendees": 10,
            "venue_capacity": 20,
            "roles": ["Host", "Helper"],
            "agenda": [
                {
                    "start_minute": 0,
                    "duration_minutes": 30,
                    "title": "Welcome",
                    "owner_role": "Host"
                }
            ],
            "data_classification": "synthetic"
        }

    def test_cli_missing_args(self):
        result = subprocess.run([sys.executable, str(self.script_path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage: python3 scripts/validate.py <plan.json>", result.stderr)

    def test_cli_too_many_args(self):
        result = subprocess.run([sys.executable, str(self.script_path), "arg1", "arg2"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage: python3 scripts/validate.py <plan.json>", result.stderr)

    def test_cli_missing_file(self):
        result = subprocess.run([sys.executable, str(self.script_path), "nonexistent.json"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_cli_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("{invalid json")
            temp_file_path = temp_file.name

        try:
            result = subprocess.run([sys.executable, str(self.script_path), temp_file_path], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        finally:
            os.remove(temp_file_path)

    def test_cli_valid_plan(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            json.dump(self.valid_plan, temp_file)
            temp_file_path = temp_file.name

        try:
            result = subprocess.run([sys.executable, str(self.script_path), temp_file_path], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS: structural checks only; no real-world activity or results verified", result.stdout)
        finally:
            os.remove(temp_file_path)

    def test_cli_invalid_plan(self):
        invalid_plan = self.valid_plan.copy()
        del invalid_plan["title"]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            json.dump(invalid_plan, temp_file)
            temp_file_path = temp_file.name

        try:
            result = subprocess.run([sys.executable, str(self.script_path), temp_file_path], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("title is required", result.stderr)
        finally:
            os.remove(temp_file_path)

    def test_cli_execution_coverage(self):
        import runpy
        import io
        from unittest.mock import patch

        # Test error scenarios
        with patch.object(sys, 'argv', ['scripts/validate.py']):
            try:
                runpy.run_path('scripts/validate.py', run_name='__main__')
            except SystemExit as e:
                self.assertIn("usage: python3 scripts/validate.py <plan.json>", str(e.code))

        with patch.object(sys, 'argv', ['scripts/validate.py', 'nonexistent.json']):
            try:
                runpy.run_path('scripts/validate.py', run_name='__main__')
            except SystemExit as e:
                self.assertIn("No such file or directory", str(e.code))

        # Test validation error scenario
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump({"kind": "event-space"}, f)
            path = f.name
        try:
            with patch.object(sys, 'argv', ['scripts/validate.py', path]):
                with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                    try:
                        runpy.run_path('scripts/validate.py', run_name='__main__')
                    except SystemExit as e:
                        self.assertEqual(e.code, 1)
                        self.assertIn("title is required", mock_stderr.getvalue())
        finally:
            os.remove(path)

        # Test success scenario
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump({
                "kind": "event-space",
                "title": "A",
                "data_classification": "synthetic",
                "expected_attendees": 1,
                "venue_capacity": 1,
                "roles": ["Host"],
                "agenda": [{"start_minute": 0, "duration_minutes": 1, "title": "A", "owner_role": "Host"}]
            }, f)
            path = f.name
        try:
            with patch.object(sys, 'argv', ['scripts/validate.py', path]):
                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    runpy.run_path('scripts/validate.py', run_name='__main__')
                    self.assertIn("PASS", mock_stdout.getvalue())
        finally:
            os.remove(path)

    def test_json_decode_error(self):
        import runpy
        from unittest.mock import patch
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("{ invalid json")
            path = f.name
        try:
            with patch.object(sys, 'argv', ['scripts/validate.py', path]):
                try:
                    runpy.run_path('scripts/validate.py', run_name='__main__')
                except SystemExit as e:
                    self.assertIn("Expecting property name", str(e.code))
        finally:
            os.remove(path)

    def test_e2e_full_workflow_valid_plan(self):
        # Generate a valid plan
        plan = self.valid_plan.copy()

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            json.dump(plan, temp_file)
            temp_file_path = temp_file.name

        try:
            # Simulate CLI validation execution
            result = subprocess.run([sys.executable, str(self.script_path), temp_file_path], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS: structural checks only", result.stdout)

            # Simulate loading the validated plan into the ingestion module
            errors = module.validate(plan)
            self.assertEqual(errors, [])
        finally:
            os.remove(temp_file_path)

    def test_e2e_full_workflow_invalid_plan(self):
        # Generate an invalid plan
        plan = self.valid_plan.copy()
        plan["venue_capacity"] = 5 # less than attendees

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            json.dump(plan, temp_file)
            temp_file_path = temp_file.name

        try:
            # Simulate CLI validation execution
            result = subprocess.run([sys.executable, str(self.script_path), temp_file_path], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("attendance exceeds the stated venue capacity", result.stderr)

            # Simulate loading the validated plan into the ingestion module
            errors = module.validate(plan)
            self.assertIn("attendance exceeds the stated venue capacity", errors)
        finally:
            os.remove(temp_file_path)
