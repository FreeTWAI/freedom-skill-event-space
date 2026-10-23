import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SkillValidation(unittest.TestCase):
    def setUp(self):
        self.skill_content = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_frontmatter_name(self):
        self.assertIn("name: freedom-event-space", self.skill_content, "Missing or incorrect name in frontmatter")

    def test_frontmatter_description(self):
        self.assertIn("description: 把讀書會、聚會或小型展演整理成場地 brief、動線與現場分工。", self.skill_content, "Missing or incorrect description in frontmatter")

    def test_structure_headers(self):
        expected_headers = [
            "# 活動與空間實作手冊",
            "## 適用範圍",
            "## 輸入",
            "## 執行步驟",
            "## 輸出與驗收",
            "## 協作交接",
            "## 邊界"
        ]
        for header in expected_headers:
            with self.subTest(header=header):
                self.assertIn(header, self.skill_content, f"Missing header: {header}")

    def test_example_invocation_commands(self):
        expected_commands = [
            "python3 scripts/validate.py examples/event-plan.json",
            "python3 -m unittest discover -s tests -v"
        ]

        # Check if the commands are inside a sh code block
        for command in expected_commands:
            with self.subTest(command=command):
                self.assertIn(command, self.skill_content, f"Missing invocation command: {command}")

        self.assertIn("```sh", self.skill_content, "Missing sh code block")

        # Check that the block contains the commands
        block_start = self.skill_content.find("```sh")
        block_end = self.skill_content.find("```", block_start + 3)
        block_content = self.skill_content[block_start:block_end]

        for command in expected_commands:
            with self.subTest(command=command):
                self.assertIn(command, block_content, f"Command {command} not found inside the shell code block")
