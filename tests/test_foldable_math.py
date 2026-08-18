#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTE_TEMPLATE_PATH = REPO_ROOT / "skill" / "paper-study" / "references" / "note-template.md"
EVALS_PATH = REPO_ROOT / "evals" / "evals.json"


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading) + len(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def _markdown_fence_after(text: str, marker: str) -> list[str]:
    remainder = text[text.index(marker) + len(marker) :]
    match = re.search(r"```markdown\n(?P<body>.*?)\n```", remainder, re.DOTALL)
    if match is None:
        raise AssertionError(f"No Markdown fence found after {marker!r}")
    return match.group("body").splitlines()


class FoldableMathSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.note_template = NOTE_TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.math_guidance = _section(
            cls.note_template,
            "### Display math inside quoted foldable annotations",
            "## Diagrams",
        )
        cls.reusable_template = _markdown_fence_after(
            cls.note_template, "Reusable foldable template with math:"
        )
        cls.evals = json.loads(EVALS_PATH.read_text(encoding="utf-8"))["evals"]

    def test_reusable_template_blockquotes_every_physical_line(self) -> None:
        self.assertTrue(self.reusable_template)
        self.assertIn(">", self.reusable_template, "Expected quoted blank separators")
        self.assertTrue(
            all(line.startswith(">") for line in self.reusable_template),
            f"Every template line must be blockquoted: {self.reusable_template!r}",
        )

    def test_reusable_template_uses_one_line_aligned_display(self) -> None:
        display_lines = [line for line in self.reusable_template if "$$" in line]

        self.assertEqual(len(display_lines), 1, display_lines)
        self.assertTrue(
            all(line.count("$$") == 2 for line in display_lines),
            "Each display must open and close on one physical Markdown line",
        )
        self.assertFalse(
            any(re.fullmatch(r">\s*\$\$\s*", line) for line in self.reusable_template),
            "The reusable template must not contain a split display delimiter",
        )
        self.assertIn(r"\begin{aligned}", display_lines[0])
        self.assertIn(r" \\ ", display_lines[0], "The two-row example needs a TeX row break")
        self.assertIn(r"\end{aligned}", display_lines[0])

    def test_guidance_distinguishes_visual_rows_from_independent_equations(self) -> None:
        self.assertRegex(
            self.math_guidance,
            r"`aligned`[^.]*one display expression[^.]*multiple visual rows",
        )
        normalized_guidance = " ".join(self.math_guidance.split())
        self.assertIn(
            "Multiple independent equations may each use their own complete one-line display",
            normalized_guidance,
        )

    def test_eval_4_keeps_the_renderer_safe_six_eval_contract(self) -> None:
        self.assertEqual(len(self.evals), 6)
        self.assertEqual({item["id"] for item in self.evals}, set(range(6)))
        eval_4 = next(item for item in self.evals if item["id"] == 4)
        prompt = eval_4["prompt"]
        expectations = "\n".join(eval_4["expectations"])

        self.assertRegex(
            prompt,
            r"一个采用 `aligned` 环境的完整展示公式[^。]*两个视觉行",
        )
        self.assertIn("VS Code Markdown 预览", prompt)
        self.assertIn("one physical Markdown source line", eval_4["expected_output"])
        self.assertIn("aligned environment", eval_4["expected_output"])
        self.assertIn("one physical source line", expectations)
        self.assertIn("TeX row breaks", expectations)
        self.assertIn("unsafe pattern", expectations)


if __name__ == "__main__":
    unittest.main()
