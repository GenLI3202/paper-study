from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("paper_study_validate", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load validator from {VALIDATOR_PATH}")
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)


REQUIRED_EVAL_KEYS = {
    "id",
    "name",
    "prompt",
    "expected_output",
    "files",
    "expectations",
}


def _skill_text(
    *,
    name: str = "paper-study",
    description: str = "Guides a careful, source-grounded academic paper study session.",
    compatibility: str = (
        "Works standalone. The teach and document-visual-enhancer skills are optional "
        "enhancements."
    ),
) -> str:
    return f"""---
name: {name}
description: >
  {description}
compatibility: >
  {compatibility}
---

# Paper Study

See the [note template](references/note-template.md) and [this section](#paper-study).
External links such as [web](https://example.com), [email](mailto:test@example.com), and
code placeholders such as [generated](<generated-path>) are not local publication links.
`[inline example](not-a-real-link.md)`

```markdown
[fenced example](also-not-a-real-link.md)
```
"""


def _eval_object(index: int) -> dict[str, object]:
    return {
        "id": index,
        "name": f"eval-{index}",
        "prompt": f"Study evals/files/fixture-{index}.md",
        "expected_output": "A source-grounded study response.",
        "files": [f"evals/files/fixture-{index}.md"],
        "expectations": ["Uses the supplied fixture."],
    }


def _write_valid_repository(root: Path) -> None:
    skill_root = root / "skill" / "paper-study"
    references = skill_root / "references"
    fixtures = root / "evals" / "files"
    references.mkdir(parents=True)
    fixtures.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text(_skill_text(), encoding="utf-8")
    (references / "note-template.md").write_text(
        "# Note template\n\nReturn to the [skill](../SKILL.md).\n",
        encoding="utf-8",
    )
    for index in range(6):
        (fixtures / f"fixture-{index}.md").write_text(
            f"# Fixture {index}\n\nSynthetic source text.\n", encoding="utf-8"
        )
    (root / "evals" / "evals.json").write_text(
        json.dumps(
            {"skill_name": "paper-study", "evals": [_eval_object(i) for i in range(6)]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_evals(root: Path) -> dict[str, object]:
    return json.loads((root / "evals" / "evals.json").read_text(encoding="utf-8"))


def _write_evals(root: Path, payload: dict[str, object]) -> None:
    (root / "evals" / "evals.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class ValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name)
        _write_valid_repository(self.root)

    def assert_error_contains(self, errors: list[str], text: str) -> None:
        self.assertTrue(
            any(text in error for error in errors),
            f"Expected an error containing {text!r}; got {errors!r}",
        )

    def test_valid_repository_passes(self) -> None:
        self.assertEqual(validate.validate_repository(self.root), [])

    def test_copy_of_current_publication_passes_without_mutating_source(self) -> None:
        shutil.rmtree(self.root)
        self.root.mkdir()
        shutil.copytree(REPO_ROOT / "skill", self.root / "skill")
        shutil.copytree(REPO_ROOT / "evals", self.root / "evals")

        self.assertEqual(validate.validate_repository(self.root), [])

    def test_required_skill_file_is_reported(self) -> None:
        (self.root / "skill" / "paper-study" / "SKILL.md").unlink()

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "required file is missing: skill/paper-study/SKILL.md")

    def test_required_nested_reference_is_reported(self) -> None:
        (self.root / "skill" / "paper-study" / "references" / "note-template.md").unlink()

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(
            errors,
            "required file is missing: skill/paper-study/references/note-template.md",
        )

    def test_frontmatter_name_must_match(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(_skill_text(name="other-skill"), encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "frontmatter name must be 'paper-study'")

    def test_frontmatter_description_must_be_nonempty(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(_skill_text(description=""), encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "frontmatter description must not be empty")

    def test_frontmatter_description_rejects_raw_angle_brackets(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(description="Study a <paper> interactively."), encoding="utf-8"
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "frontmatter description contains raw angle brackets")

    def test_frontmatter_compatibility_must_say_standalone(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Requires another runtime. The teach and document-visual-enhancer skills "
                    "are optional enhancements."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "frontmatter compatibility must say standalone")

    def test_missing_frontmatter_is_reported_cleanly(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text("# No frontmatter\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "SKILL.md must start with YAML frontmatter")

    def test_eval_count_must_be_exactly_six(self) -> None:
        payload = _read_evals(self.root)
        payload["evals"] = payload["evals"][:5]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "evals.json must contain exactly 6 eval objects")

    def test_eval_ids_must_be_unique(self) -> None:
        payload = _read_evals(self.root)
        evals = payload["evals"]
        evals[1]["id"] = evals[0]["id"]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval IDs must be unique")

    def test_eval_objects_must_have_all_required_keys(self) -> None:
        payload = _read_evals(self.root)
        del payload["evals"][0]["expectations"]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 is missing required keys: expectations")
        self.assertEqual(REQUIRED_EVAL_KEYS - set(payload["evals"][0]), {"expectations"})  # type: ignore[index]

    def test_malformed_eval_json_is_reported_cleanly(self) -> None:
        (self.root / "evals" / "evals.json").write_text("{broken", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "evals/evals.json is not valid JSON")

    def test_missing_eval_fixture_is_reported(self) -> None:
        (self.root / "evals" / "files" / "fixture-0.md").unlink()

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 fixture does not exist")

    def test_eval_fixture_cannot_escape_fixture_directory(self) -> None:
        outside = self.root / "evals" / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        payload = _read_evals(self.root)
        payload["evals"][0]["files"] = ["evals/files/../outside.md"]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 fixture must stay under evals/files")

    def test_broken_local_markdown_link_is_reported(self) -> None:
        reference = self.root / "skill" / "paper-study" / "references" / "note-template.md"
        reference.write_text("[missing](missing.md)\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "broken local Markdown link")
        self.assert_error_contains(errors, "references/note-template.md")

    def test_forbidden_publication_markers_are_rejected(self) -> None:
        markers = [
            "/Users/",
            "paper-study-workspace",
            "originSessionId",
            "LEMS",
            "Optimal Battery Bidding",
        ]
        for marker in markers:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                fixture = root / "evals" / "files" / "fixture-0.md"
                fixture.write_text(f"Synthetic content leaked {marker}\n", encoding="utf-8")

                errors = validate.validate_repository(root)

                self.assert_error_contains(errors, f"forbidden publication text {marker!r}")

    def test_repository_readmes_are_included_in_publication_scan(self) -> None:
        (self.root / "README.md").write_text(
            "Publication instructions leaked originSessionId.\n", encoding="utf-8"
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "forbidden publication text 'originSessionId'")
        self.assert_error_contains(errors, "README.md")

    def test_package_source_allowlist_rejects_extra_file(self) -> None:
        extra = self.root / "skill" / "paper-study" / "helper.py"
        extra.write_text("pass\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "package source is not allowlisted: helper.py")

    def test_teach_dependency_must_be_optional_or_conditional(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is required. The "
                    "document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(
            errors, "dependency 'teach' must be described as optional or conditional"
        )

    def test_visual_dependency_must_be_optional_or_conditional(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional. The "
                    "document-visual-enhancer skill is required."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(
            errors,
            "dependency 'document-visual-enhancer' must be described as optional or conditional",
        )

    def test_cli_accepts_repo_root_and_reports_success(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Validation passed", completed.stdout)

    def test_cli_prints_clear_failures_and_returns_nonzero(self) -> None:
        (self.root / "skill" / "paper-study" / "SKILL.md").unlink()
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = validate.main([str(self.root)])

        self.assertNotEqual(exit_code, 0)
        self.assertIn("Validation failed", output.getvalue())
        self.assertIn("required file is missing", output.getvalue())

    def test_github_workflow_runs_tests_validator_and_coverage_gate(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python scripts/validate.py", workflow)
        self.assertIn("python -m pip install coverage", workflow)
        self.assertIn(
            "python -m coverage run --branch -m unittest discover -s tests -v", workflow
        )
        self.assertIn("python -m coverage report --fail-under=80", workflow)


if __name__ == "__main__":
    unittest.main()
