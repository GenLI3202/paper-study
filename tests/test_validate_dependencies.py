from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_validate as shared


validate = shared.validate
_skill_text = shared._skill_text
_write_valid_repository = shared._write_valid_repository


class DependencyPolicyValidatorTestCase(unittest.TestCase):
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

    def test_negated_optional_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is not optional. The "
                    "document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not negate optionality")

    def test_contracted_or_contradictory_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional but is also required. "
                    "The document-visual-enhancer skill isn't optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")
        self.assert_error_contains(
            errors,
            "dependency 'document-visual-enhancer' must not negate optionality",
        )

    def test_obligatory_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional but must be installed. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_required_before_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. It is required to install the teach skill. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_negated_obligation_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional and must not be installed. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_not_only_required_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional but not only required; it "
                    "is also recommended. The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_not_mandatory_dependency_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional, not mandatory. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_has_to_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional but has to be installed. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_rather_than_required_dependency_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional rather than required. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_explicit_not_required_dependency_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional and is not required. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_user_installation_obligation_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional, but users have to install "
                    "teach. The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_prerequisite_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional, but teach is a prerequisite. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_as_opposed_to_required_dependency_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional as opposed to required. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_negative_capability_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is optional, but without teach this "
                    "skill cannot run. The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not be required")

    def test_no_dependency_is_required_wording_is_allowed(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. No teach skill is required; teach remains optional. "
                    "The document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assertNotIn("dependency 'teach' must not be required", errors)

    def test_no_longer_optional_dependency_wording_is_rejected(self) -> None:
        skill = self.root / "skill" / "paper-study" / "SKILL.md"
        skill.write_text(
            _skill_text(
                compatibility=(
                    "Works standalone. The teach skill is no longer optional. The "
                    "document-visual-enhancer skill is optional."
                )
            ),
            encoding="utf-8",
        )

        errors = validate.validate_repository(self.root)

        self.assert_error_contains(errors, "dependency 'teach' must not negate optionality")

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


if __name__ == "__main__":
    unittest.main()
