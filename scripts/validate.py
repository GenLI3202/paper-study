from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote


SKILL_ROOT = Path("skill/paper-study")
REQUIRED_FILES = (
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "references/note-template.md",
    Path("evals/evals.json"),
)
REQUIRED_EVAL_KEYS = frozenset(
    {"id", "name", "prompt", "expected_output", "files", "expectations"}
)
FORBIDDEN_PUBLICATION_TEXT = (
    "/Users/",
    "paper-study-workspace",
    "originSessionId",
    "LEMS",
    "Optimal Battery Bidding",
)
OPTIONAL_DEPENDENCIES = ("teach", "document-visual-enhancer")
TEXT_SUFFIXES = frozenset({".json", ".md", ".txt", ".yaml", ".yml"})
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FRONTMATTER_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _read_text(path: Path, root: Path) -> tuple[str | None, list[str]]:
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError) as exc:
        display = _display_path(path, root)
        return None, [f"could not read {display} as UTF-8: {exc}"]


def _validate_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"required file is missing: {relative.as_posix()}")
    return errors


def _validate_package_allowlist(root: Path) -> list[str]:
    package_root = root / SKILL_ROOT
    if not package_root.is_dir():
        return []
    errors: list[str] = []
    for path in sorted(package_root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(package_root)
        allowed = relative == Path("SKILL.md") or (
            len(relative.parts) > 1 and relative.parts[0] == "references"
        )
        if not allowed:
            errors.append(f"package source is not allowlisted: {relative.as_posix()}")
        elif path.is_symlink():
            errors.append(f"package source must not be a symlink: {relative.as_posix()}")
    return errors


def _scalar_value(raw_value: str) -> str:
    value = raw_value.strip()
    if value in {">", ">-", ">+", "|", "|-", "|+"}:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str] | None, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["SKILL.md must start with YAML frontmatter"]
    try:
        closing_index = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, ["SKILL.md frontmatter is missing its closing delimiter"]

    fields: dict[str, str] = {}
    current_key: str | None = None
    errors: list[str] = []
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        match = FRONTMATTER_KEY.match(line)
        if match:
            current_key = match.group(1)
            if current_key in fields:
                errors.append(f"SKILL.md frontmatter repeats key {current_key!r}")
            fields[current_key] = _scalar_value(match.group(2) or "")
        elif not line.strip():
            continue
        elif line[:1].isspace() and current_key is not None:
            fields[current_key] = " ".join((fields[current_key], line.strip())).strip()
        else:
            errors.append(f"SKILL.md frontmatter line {line_number} is not supported")
    return fields, errors


def _validate_frontmatter(root: Path) -> list[str]:
    skill_path = root / SKILL_ROOT / "SKILL.md"
    if not skill_path.is_file() or skill_path.is_symlink():
        return []
    text, errors = _read_text(skill_path, root)
    if text is None:
        return errors
    fields, parse_errors = _parse_frontmatter(text)
    if fields is None:
        return errors + parse_errors

    result = errors + parse_errors
    if fields.get("name") != "paper-study":
        result.append("frontmatter name must be 'paper-study'")
    description = fields.get("description", "").strip()
    if not description:
        result.append("frontmatter description must not be empty")
    elif "<" in description or ">" in description:
        result.append("frontmatter description contains raw angle brackets")
    if not re.search(r"\bstandalone\b", fields.get("compatibility", ""), re.IGNORECASE):
        result.append("frontmatter compatibility must say standalone")
    return result


def _load_eval_document(root: Path) -> tuple[dict[str, object] | None, list[str]]:
    path = root / "evals/evals.json"
    if not path.is_file() or path.is_symlink():
        return None, []
    text, errors = _read_text(path, root)
    if text is None:
        return None, errors
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"evals/evals.json is not valid JSON: {exc.msg}"]
    if not isinstance(payload, dict):
        return None, ["evals/evals.json must contain a JSON object"]
    return payload, []


def _validate_eval_objects(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if payload.get("skill_name") != "paper-study":
        errors.append("evals.json skill_name must be 'paper-study'")
    evals = payload.get("evals")
    if not isinstance(evals, list):
        return errors + ["evals.json must contain exactly 6 eval objects"]
    if len(evals) != 6:
        errors.append("evals.json must contain exactly 6 eval objects")

    identifiers: list[str | int] = []
    for index, eval_object in enumerate(evals):
        if not isinstance(eval_object, dict):
            errors.append(f"eval {index} must be a JSON object")
            continue
        missing = sorted(REQUIRED_EVAL_KEYS - eval_object.keys())
        if missing:
            errors.append(f"eval {index} is missing required keys: {', '.join(missing)}")
        identifier = eval_object.get("id")
        if isinstance(identifier, bool) or not isinstance(identifier, (int, str)):
            errors.append(f"eval {index} ID must be a string or integer")
        elif identifier in identifiers:
            errors.append("eval IDs must be unique")
        else:
            identifiers.append(identifier)
    return errors


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def _validate_eval_fixtures(root: Path, payload: dict[str, object]) -> list[str]:
    evals = payload.get("evals")
    if not isinstance(evals, list):
        return []
    fixture_root = (root / "evals/files").resolve()
    errors: list[str] = []
    for index, eval_object in enumerate(evals):
        if not isinstance(eval_object, dict):
            continue
        references = eval_object.get("files")
        if not isinstance(references, list):
            errors.append(f"eval {index} files must be a JSON array")
            continue
        for reference in references:
            errors += _validate_fixture_reference(root, fixture_root, index, reference)
    return errors


def _validate_fixture_reference(
    root: Path, fixture_root: Path, index: int, reference: object
) -> list[str]:
    if not isinstance(reference, str) or not reference.strip():
        return [f"eval {index} fixture path must be a nonempty string"]
    reference_path = Path(reference)
    if reference_path.is_absolute():
        return [f"eval {index} fixture must stay under evals/files: {reference}"]
    try:
        candidate = (root / reference_path).resolve()
    except (OSError, RuntimeError):
        return [f"eval {index} fixture cannot be resolved: {reference}"]
    if not _is_within(candidate, fixture_root):
        return [f"eval {index} fixture must stay under evals/files: {reference}"]
    if not candidate.is_file():
        return [f"eval {index} fixture does not exist: {reference}"]
    return []


def _publication_files(root: Path) -> tuple[Path, ...]:
    files: set[Path] = set()
    for relative_root in (SKILL_ROOT, Path("evals")):
        directory = root / relative_root
        if directory.is_dir():
            files.update(path for path in directory.rglob("*") if path.is_file())
    files.update(path for path in root.glob("README*.md") if path.is_file())
    return tuple(sorted(files))


def _markdown_without_code(text: str) -> str:
    visible_lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            visible_lines.append("")
        elif in_fence:
            visible_lines.append("")
        else:
            visible_lines.append(re.sub(r"`+[^`\n]*`+", "", line))
    return "\n".join(visible_lines)


def _link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        enclosed = target[1:-1].strip()
        if "/" not in enclosed and "." not in Path(enclosed).name:
            return None
        target = enclosed
    else:
        target = target.split(maxsplit=1)[0]
    if not target or target.startswith(("#", "//")) or URL_SCHEME.match(target):
        return None
    if "<" in target or ">" in target or "{" in target or "}" in target:
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0]) or None


def _validate_markdown_links(root: Path, files: tuple[Path, ...]) -> list[str]:
    errors: list[str] = []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text, read_errors = _read_text(path, root)
        errors += read_errors
        if text is None:
            continue
        visible_text = _markdown_without_code(text)
        for match in MARKDOWN_LINK.finditer(visible_text):
            target = _link_target(match.group(1))
            if target is not None and not (path.parent / target).exists():
                display = _display_path(path, root)
                errors.append(f"broken local Markdown link in {display}: {target}")
    return errors


def _validate_forbidden_text(root: Path, files: tuple[Path, ...]) -> list[str]:
    errors: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text, read_errors = _read_text(path, root)
        errors += read_errors
        if text is None:
            continue
        display = _display_path(path, root)
        for forbidden in FORBIDDEN_PUBLICATION_TEXT:
            if forbidden in text:
                errors.append(f"forbidden publication text {forbidden!r} in {display}")
    return errors


def _dependency_is_conditional(text: str, dependency: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.replace("`", " "))
    segments = re.split(r"(?<=[.!?;])\s+", normalized)
    for segment in segments:
        lowered = segment.lower()
        if dependency.lower() not in lowered:
            continue
        if "optional" in lowered:
            return True
        if re.search(r"\b(?:can|may)\s+enhance\b", lowered):
            return True
        if re.search(r"\b(?:if|when)\b.{0,160}\bavailable\b", lowered):
            return True
    return False


def _validate_optional_dependencies(root: Path, files: tuple[Path, ...]) -> list[str]:
    package_markdown = [
        path for path in files if _is_within(path, root / SKILL_ROOT) and path.suffix == ".md"
    ]
    texts: list[str] = []
    errors: list[str] = []
    for path in package_markdown:
        text, read_errors = _read_text(path, root)
        errors += read_errors
        if text is not None:
            texts.append(text)
    combined = "\n".join(texts)
    for dependency in OPTIONAL_DEPENDENCIES:
        if not _dependency_is_conditional(combined, dependency):
            errors.append(
                f"dependency {dependency!r} must be described as optional or conditional"
            )
    return errors


def validate_repository(repo_root: str | Path) -> list[str]:
    root = Path(repo_root).expanduser().resolve()
    if not root.is_dir():
        return [f"repository root is not a directory: {root}"]

    errors = _validate_required_files(root)
    errors += _validate_package_allowlist(root)
    errors += _validate_frontmatter(root)
    payload, eval_errors = _load_eval_document(root)
    errors += eval_errors
    if payload is not None:
        errors += _validate_eval_objects(payload)
        errors += _validate_eval_fixtures(root, payload)
    publication_files = _publication_files(root)
    errors += _validate_markdown_links(root, publication_files)
    errors += _validate_forbidden_text(root, publication_files)
    errors += _validate_optional_dependencies(root, publication_files)
    return errors


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the paper-study publication package.")
    parser.add_argument(
        "repo_root",
        nargs="?",
        type=Path,
        default=_default_repo_root(),
        help="repository root (defaults to the parent of scripts/)",
    )
    arguments = parser.parse_args(argv)
    root = arguments.repo_root.expanduser().resolve()
    errors = validate_repository(root)
    if errors:
        print(f"Validation failed for {root} with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
