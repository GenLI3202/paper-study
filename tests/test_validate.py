from __future__ import annotations

import configparser
import importlib.util
import io
import json
import re
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
        "# Note template\n\nUse this synthetic template.\n",
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

    def test_eval_id_must_be_an_integer(self) -> None:
        payload = _read_evals(self.root)
        payload["evals"][0]["id"] = "zero"  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 id must be an integer")

    def test_eval_scalar_fields_require_nonempty_strings(self) -> None:
        invalid_values = {"name": "  ", "prompt": 7, "expected_output": ""}
        for field, value in invalid_values.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                payload = _read_evals(root)
                payload["evals"][0][field] = value  # type: ignore[index]
                _write_evals(root, payload)

                errors = validate.validate_repository(root)

                self.assert_error_contains(
                    errors, f"eval 0 {field} must be a nonempty string"
                )

    def test_eval_list_fields_require_nonempty_string_items(self) -> None:
        invalid_values = {
            "files": [],
            "expectations": ["valid", "  "],
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                payload = _read_evals(root)
                payload["evals"][0][field] = value  # type: ignore[index]
                _write_evals(root, payload)

                errors = validate.validate_repository(root)

                self.assert_error_contains(
                    errors, f"eval 0 {field} must be a nonempty list of nonempty strings"
                )

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

    def test_eval_fixture_root_cannot_resolve_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as outside_directory:
            fixture_root = self.root / "evals" / "files"
            shutil.rmtree(fixture_root)
            outside = Path(outside_directory)
            for index in range(6):
                (outside / f"fixture-{index}.md").write_text("# External\n", encoding="utf-8")
            fixture_root.symlink_to(outside, target_is_directory=True)

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval fixture directory resolves outside repository")

    def test_nul_eval_fixture_path_is_reported_without_exception(self) -> None:
        payload = _read_evals(self.root)
        payload["evals"][0]["files"] = ["evals/files/bad\0name.md"]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 fixture path contains NUL")

    def test_eval_fixture_rejects_unsupported_text_format(self) -> None:
        fixture = self.root / "evals" / "files" / "leak.html"
        fixture.write_text("Synthetic HTML fixture.\n", encoding="utf-8")
        payload = _read_evals(self.root)
        payload["evals"][0]["files"] = ["evals/files/leak.html"]  # type: ignore[index]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "eval 0 fixture must use a supported text format")

    def test_fixture_directory_named_like_workspace_is_still_scanned(self) -> None:
        fixture = self.root / "evals" / "files" / "paper-study-workspace" / "hidden.md"
        fixture.parent.mkdir()
        marker = "/" + "Users" + "/"
        fixture.write_text(f"Synthetic leak: {marker}private\n", encoding="utf-8")
        payload = _read_evals(self.root)
        payload["evals"][0]["files"] = [  # type: ignore[index]
            "evals/files/paper-study-workspace/hidden.md"
        ]
        _write_evals(self.root, payload)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, f"forbidden publication text {marker!r}")

    def test_broken_local_markdown_link_is_reported(self) -> None:
        reference = self.root / "skill" / "paper-study" / "references" / "note-template.md"
        reference.write_text("[missing](missing.md)\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "broken local Markdown link")
        self.assert_error_contains(errors, "references/note-template.md")

    def test_absolute_markdown_link_is_rejected_even_when_it_exists(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as outside:
            readme = self.root / "README.md"
            readme.write_text(f"[outside]({outside.name})\n", encoding="utf-8")

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "local Markdown link must be relative")

    def test_traversing_markdown_link_is_rejected(self) -> None:
        reference = self.root / "skill" / "paper-study" / "references" / "note-template.md"
        reference.write_text("[skill](../SKILL.md)\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "local Markdown link must not traverse directories")

    def test_markdown_link_cannot_resolve_outside_repository(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as outside:
            linked = self.root / "linked.md"
            linked.symlink_to(outside.name)
            (self.root / "README.md").write_text("[outside](linked.md)\n", encoding="utf-8")

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "local Markdown link resolves outside repository")

    def test_forbidden_publication_markers_are_rejected(self) -> None:
        markers = [
            "/" + "Users" + "/",
            "origin" + "SessionId",
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
        marker = "origin" + "SessionId"
        (self.root / "README.md").write_text(
            f"Publication instructions leaked {marker}.\n", encoding="utf-8"
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, f"forbidden publication text {marker!r}")
        self.assert_error_contains(errors, "README.md")

    def test_publication_symlink_is_rejected_instead_of_skipped(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as outside:
            Path(outside.name).write_text("External publication text.\n", encoding="utf-8")
            (self.root / "README.md").symlink_to(outside.name)

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "publication path must not be a symlink: README.md")

    def test_excluded_publication_root_must_not_be_a_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as outside_directory:
            workspace = self.root / "paper-study-workspace"
            workspace.symlink_to(outside_directory, target_is_directory=True)

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(
            errors,
            "publication path must not be a symlink: paper-study-workspace",
        )

    def test_fixed_eval_parent_directory_must_not_be_a_symlink(self) -> None:
        target = self.root / "internal-evals"
        shutil.copytree(self.root / "evals", target)
        shutil.rmtree(self.root / "evals")
        (self.root / "evals").symlink_to(target, target_is_directory=True)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "required directory must not be a symlink: evals")

    def test_fixed_reference_parent_directory_must_not_be_a_symlink(self) -> None:
        references = self.root / "skill" / "paper-study" / "references"
        target = self.root / "internal-references"
        shutil.copytree(references, target)
        shutil.rmtree(references)
        references.symlink_to(target, target_is_directory=True)

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(
            errors,
            "required directory must not be a symlink: skill/paper-study/references",
        )

    def test_scripts_and_workflows_are_included_in_publication_scan(self) -> None:
        marker = "/" + "Users" + "/"
        script = self.root / "scripts" / "helper.py"
        workflow = self.root / ".github" / "workflows" / "check.yml"
        script.parent.mkdir(parents=True)
        workflow.parent.mkdir(parents=True)
        script.write_text(f'PRIVATE_PATH = "{marker}example"\n', encoding="utf-8")
        workflow.write_text("name: Safe\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, f"forbidden publication text {marker!r}")
        self.assert_error_contains(errors, "scripts/helper.py")

    def test_package_source_allowlist_rejects_extra_file(self) -> None:
        extra = self.root / "skill" / "paper-study" / "helper.py"
        extra.write_text("pass\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "package source is not allowlisted: helper.py")

    def test_package_manifest_rejects_extra_reference_file(self) -> None:
        extra = self.root / "skill" / "paper-study" / "references" / "extra.md"
        extra.write_text("# Extra\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "package source is not allowlisted: references/extra.md")

    def test_package_rejects_directory_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as outside_directory:
            link = self.root / "skill" / "paper-study" / "references" / "linked-directory"
            link.symlink_to(outside_directory, target_is_directory=True)

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "package directory must not be a symlink")

    def test_package_root_cannot_resolve_outside_repository(self) -> None:
        package_root = self.root / "skill" / "paper-study"
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "paper-study"
            (outside / "references").mkdir(parents=True)
            (outside / "SKILL.md").write_text(_skill_text(), encoding="utf-8")
            (outside / "references" / "note-template.md").write_text(
                "# External template\n", encoding="utf-8"
            )
            shutil.rmtree(package_root)
            package_root.symlink_to(outside, target_is_directory=True)

            errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "package source resolves outside repository")


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

    def test_coverage_configuration_measures_scripts_and_enforces_gate(self) -> None:
        configuration = configparser.ConfigParser()
        loaded = configuration.read(REPO_ROOT / ".coveragerc", encoding="utf-8")

        self.assertEqual(loaded, [str(REPO_ROOT / ".coveragerc")])
        self.assertTrue(configuration.getboolean("run", "branch"))
        self.assertEqual(configuration.get("run", "source").strip(), "scripts")
        self.assertEqual(configuration.getint("report", "fail_under"), 80)

    def test_release_sections_are_short_and_require_verification_before_extraction(self) -> None:
        cases = (
            (
                "README.md",
                "### Release archive",
                r"before (?:extracting|installation), verify[^.\n]*sha-256",
            ),
            (
                "README.zh-CN.md",
                "### Release 压缩包",
                r"解压前先核验[^。\n]*sha-256",
            ),
        )
        for relative, heading, verification_pattern in cases:
            with self.subTest(relative=relative):
                readme = (REPO_ROOT / relative).read_text(encoding="utf-8")
                start = readme.index(heading)
                following = readme[start + len(heading) :]
                next_section = re.search(r"^#{1,3}(?:\s|$)", following, re.MULTILINE)
                section = following[: next_section.start()] if next_section else following
                fences = re.findall(
                    r"```(?P<language>[^\n]*)\n(?P<body>.*?)\n```",
                    section,
                    re.DOTALL,
                )

                self.assertLessEqual(len(section.splitlines()), 15)
                self.assertNotIn("~~~", section)
                self.assertEqual(
                    fences,
                    [
                        (
                            "text",
                            "paper-study/SKILL.md\n"
                            "paper-study/references/note-template.md",
                        )
                    ],
                )
                self.assertRegex(
                    section,
                    re.compile(verification_pattern, re.IGNORECASE),
                )
                self.assertIn("v0.1.1", section)
                self.assertIn("paper-study.skill", section)
                self.assertIn("SHA256SUMS", section)
                self.assertIn("paper-study/SKILL.md", section)
                self.assertIn("paper-study/references/note-template.md", section)

    def test_generated_workspace_is_consistently_ignored(self) -> None:
        ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

        self.assertIn("paper-study-workspace/", ignore)
        self.assertIn(Path("paper-study-workspace"), validate.EXCLUDED_PUBLICATION_ROOTS)
        self.assertIn(
            Path("skill/paper-study-workspace"), validate.EXCLUDED_PUBLICATION_ROOTS
        )

    def test_github_workflow_builds_and_uploads_verified_release_assets(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python scripts/validate.py", workflow)
        self.assertIn(
            "python -m pip install coverage==7.15.4 PyYAML==6.0.3", workflow
        )
        self.assertIn("python -m coverage run -m unittest discover -s tests -v", workflow)
        self.assertIn("python -m coverage report", workflow)
        self.assertIn("yaml.safe_load", workflow)
        self.assertIn('Path("skill/paper-study/SKILL.md")', workflow)
        self.assertIn('source = Path("skill/paper-study")', workflow)
        self.assertIn('"paper-study/SKILL.md"', workflow)
        self.assertIn('"paper-study/references/note-template.md"', workflow)
        self.assertIn("names != expected_archive", workflow)
        self.assertIn('len(metadata["compatibility"]) > 500', workflow)
        self.assertIn("hashlib.sha256", workflow)
        self.assertIn('Path("dist")', workflow)
        self.assertIn("dist/SHA256SUMS", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn('name: paper-study-${{ github.sha }}', workflow)
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main'",
            workflow,
        )
        self.assertIn("if-no-files-found: error", workflow)
        self.assertNotIn("repository: anthropics/skills", workflow)


if __name__ == "__main__":
    unittest.main()
