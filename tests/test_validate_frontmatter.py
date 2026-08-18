from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import test_validate as shared


validate = shared.validate
_skill_text = shared._skill_text
_write_valid_repository = shared._write_valid_repository


class FrontmatterValidatorTestCase(unittest.TestCase):
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

    def test_frontmatter_rejects_negated_standalone_claim(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "This skill is not standalone. The teach and document-visual-enhancer "
                    "skills are optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "compatibility must not negate standalone")

    def test_frontmatter_rejects_standalone_negation_variants(self) -> None:
        cases = (
            "Cannot be used standalone.",
            "Fails to work standalone.",
            "Standalone use is unsupported.",
            "Standalone use isn't supported.",
            "Standalone use isn’t supported.",
        )
        for claim in cases:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                skill = root / "skill" / "paper-study" / "SKILL.md"
                skill.write_text(
                    _skill_text(
                        compatibility=(
                            f"{claim} The teach and document-visual-enhancer skills are optional."
                        )
                    ),
                    encoding="utf-8",
                )

                errors = validate.validate_repository(root)

                self.assert_error_contains(errors, "compatibility must not negate standalone")

    def test_frontmatter_rejects_never_works_standalone(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "This skill never works standalone. The teach and "
                    "document-visual-enhancer skills are optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "compatibility must not negate standalone")

    def test_frontmatter_accepts_explicit_skill_subject(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "This skill works standalone. The teach and "
                    "document-visual-enhancer skills are optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("frontmatter compatibility must say standalone", errors)
        self.assertNotIn("frontmatter compatibility must not negate standalone", errors)

    def test_frontmatter_rejects_conditionally_standalone_claim(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone only when teach is available. The teach and "
                    "document-visual-enhancer skills are optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "compatibility must not negate standalone")

    def test_standalone_claim_does_not_capture_later_negation(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone and never requires teach. The teach and "
                    "document-visual-enhancer skills are optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("frontmatter compatibility must not negate standalone", errors)

    def test_frontmatter_rejects_unsupported_key(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        content = _skill_text().replace("name: paper-study\n", "name: paper-study\nextra: true\n")
        skill.write_text(content, encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "unsupported frontmatter key: extra")

    def test_frontmatter_rejects_malformed_plain_scalars(self) -> None:
        invalid_values = (
            "foo: bar",
            "- invalid",
            "%invalid",
            "| text",
            "'foo'bar'",
            "]invalid",
            "}invalid",
            ",invalid",
        )
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                skill = root / "skill" / "paper-study" / "SKILL.md"
                content = _skill_text().replace(
                    "description: >\n  Guides a careful, source-grounded academic paper study session.",
                    f"description: {value}",
                )
                skill.write_text(content, encoding="utf-8")

                errors = validate.validate_repository(root)

                self.assert_error_contains(errors, "unsupported YAML frontmatter")

    def test_frontmatter_rejects_yaml_sequences_in_supported_subset(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        content = _skill_text().replace(
            "description: >\n  Guides a careful, source-grounded academic paper study session.",
            "description:\n  - invalid sequence",
        )
        skill.write_text(content, encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "unsupported YAML frontmatter")

    def test_frontmatter_rejects_yaml_comment_as_description(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        content = _skill_text().replace(
            "description: >\n  Guides a careful, source-grounded academic paper study session.",
            "description: # intentionally blank",
        )
        skill.write_text(content, encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "unsupported YAML frontmatter")
        self.assert_error_contains(errors, "frontmatter description must not be empty")

    def test_frontmatter_rejects_extra_block_indentation(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        prefix = (
            "Works standalone. The teach and document-visual-enhancer skills are optional "
            "enhancements."
        )
        content = _skill_text().replace(
            "compatibility: >\n  " + prefix,
            "compatibility: >\n    " + prefix,
        )
        skill.write_text(content, encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "unsupported YAML frontmatter")

    def test_frontmatter_enforces_official_length_limits(self) -> None:
        cases = (
            (
                "description",
                {"description": "x" * 1025},
                "description exceeds 1024 characters",
            ),
            (
                "compatibility",
                {
                    "compatibility": (
                        "Works standalone. The teach and document-visual-enhancer skills are "
                        "optional enhancements. " + "x" * 501
                    )
                },
                "compatibility exceeds 500 characters",
            ),
        )
        for label, arguments, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                skill = root / "skill" / "paper-study" / "SKILL.md"
                skill.write_text(_skill_text(**arguments), encoding="utf-8")

                errors = validate.validate_repository(root)

                self.assert_error_contains(errors, expected)

    def test_frontmatter_length_boundaries_match_decoded_yaml(self) -> None:
        prefix = (
            "Works standalone. The teach and document-visual-enhancer skills are optional "
            "enhancements."
        )
        cases = (
            ("quoted-500", json.dumps(prefix.ljust(500)), False),
            ("quoted-501", json.dumps(prefix.ljust(501)), True),
            ("block-500", ">\n  " + prefix.ljust(499), False),
            ("block-501", ">\n  " + prefix.ljust(500), True),
        )
        for label, yaml_value, should_fail in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _write_valid_repository(root)
                skill = root / "skill" / "paper-study" / "SKILL.md"
                content = _skill_text().replace(
                    "compatibility: >\n  " + prefix,
                    f"compatibility: {yaml_value}",
                )
                skill.write_text(content, encoding="utf-8")

                errors = validate.validate_repository(root)
                has_length_error = any(
                    "compatibility exceeds 500 characters" in error for error in errors
                )

                self.assertEqual(has_length_error, should_fail, errors)

    def test_missing_frontmatter_is_reported_cleanly(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text("# No frontmatter\n", encoding="utf-8")

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "SKILL.md must start with YAML frontmatter")


if __name__ == "__main__":
    unittest.main()
