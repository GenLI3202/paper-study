from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote


SKILL_ROOT = Path("skill/paper-study")
PACKAGE_MANIFEST = frozenset({"SKILL.md", "references/note-template.md"})
REQUIRED_FILES = (
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "references/note-template.md",
    Path("evals/evals.json"),
)
REQUIRED_EVAL_KEYS = frozenset(
    {"id", "name", "prompt", "expected_output", "files", "expectations"}
)
EVAL_STRING_FIELDS = ("name", "prompt", "expected_output")
EVAL_LIST_FIELDS = ("files", "expectations")
SUPPORTED_FRONTMATTER_KEYS = frozenset({"name", "description", "compatibility"})
FORBIDDEN_PUBLICATION_TEXT = (
    "/" + "Users" + "/",
    "origin" + "SessionId",
)
OPTIONAL_DEPENDENCIES = ("teach", "document-visual-enhancer")
TEXT_SUFFIXES = frozenset(
    {".csv", ".json", ".md", ".py", ".rst", ".toml", ".txt", ".yaml", ".yml"}
)
TEXT_FILENAMES = frozenset({".coveragerc", ".gitignore", "LICENSE"})
EXCLUDED_PUBLICATION_DIRS = frozenset({".git", ".official-skills", "__pycache__", "dist"})
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
FRONTMATTER_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")
YAML_IMPLICIT_NONSTRING = re.compile(
    r"^(?:null|true|false|yes|no|on|off|~|[-+]?\d+(?:\.\d+)?)$", re.IGNORECASE
)


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
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError, ValueError):
            errors.append(f"required file cannot be resolved: {relative.as_posix()}")
            continue
        if not _is_within(resolved, root):
            errors.append(f"required source resolves outside repository: {relative.as_posix()}")
        if not path.is_file() or path.is_symlink():
            errors.append(f"required file is missing: {relative.as_posix()}")
    return errors


def _validate_package_allowlist(root: Path) -> list[str]:
    package_root = root / SKILL_ROOT
    if not package_root.is_dir():
        return []
    errors: list[str] = []
    try:
        resolved_root = package_root.resolve()
    except (OSError, RuntimeError, ValueError):
        return ["package source cannot be resolved"]
    if package_root.is_symlink():
        errors.append("package directory must not be a symlink: skill/paper-study")
    if not _is_within(resolved_root, root):
        errors.append("package source resolves outside repository: skill/paper-study")
        return errors

    for path in sorted(package_root.rglob("*")):
        relative = path.relative_to(package_root)
        display = relative.as_posix()
        if path.is_symlink():
            kind = "directory" if path.is_dir() else "source"
            errors.append(f"package {kind} must not be a symlink: {display}")
            try:
                resolved = path.resolve()
            except (OSError, RuntimeError, ValueError):
                errors.append(f"package source cannot be resolved: {display}")
            else:
                if not _is_within(resolved, root):
                    errors.append(f"package source resolves outside repository: {display}")
            continue
        if path.is_dir():
            continue
        if display not in PACKAGE_MANIFEST:
            errors.append(f"package source is not allowlisted: {display}")
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError, ValueError):
            errors.append(f"package source cannot be resolved: {display}")
        else:
            if not _is_within(resolved, root):
                errors.append(f"package source resolves outside repository: {display}")
    return errors


def _parse_frontmatter_scalar(
    raw_value: str, line_number: int
) -> tuple[str, bool, list[str]]:
    value = raw_value.strip()
    if value in {">", ">-", ">+", "|", "|-", "|+"}:
        return "", True, []
    if not value:
        return "", False, []
    if value[0] in {'"', "'"}:
        if len(value) < 2 or value[-1] != value[0]:
            return "", False, [f"unsupported YAML frontmatter at line {line_number}: quote"]
        if value[0] == '"':
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return "", False, [
                    f"unsupported YAML frontmatter at line {line_number}: quoted scalar"
                ]
            return parsed, False, []
        return value[1:-1].replace("''", "'"), False, []
    if value[0] in "[{!&*" or " #" in value or YAML_IMPLICIT_NONSTRING.fullmatch(value):
        return "", False, [f"unsupported YAML frontmatter at line {line_number}: scalar"]
    return value, False, []


def _parse_frontmatter(text: str) -> tuple[dict[str, str] | None, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None, ["SKILL.md must start with YAML frontmatter"]
    try:
        closing_index = next(i for i in range(1, len(lines)) if lines[i] == "---")
    except StopIteration:
        return None, ["SKILL.md frontmatter is missing its closing delimiter"]

    fields: dict[str, str] = {}
    block_key: str | None = None
    errors: list[str] = []
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        if "\t" in line:
            errors.append(f"unsupported YAML frontmatter at line {line_number}: tab")
            continue
        match = FRONTMATTER_KEY.match(line)
        if match:
            key = match.group(1)
            if key not in SUPPORTED_FRONTMATTER_KEYS:
                errors.append(f"unsupported frontmatter key: {key}")
            if key in fields:
                errors.append(f"SKILL.md frontmatter repeats key {key!r}")
            value, is_block, scalar_errors = _parse_frontmatter_scalar(
                match.group(2) or "", line_number
            )
            fields[key] = value
            block_key = key if is_block else None
            errors += scalar_errors
        elif not line.strip():
            continue
        elif line[:1].isspace() and block_key is not None:
            fields[block_key] = " ".join((fields[block_key], line.strip())).strip()
        else:
            errors.append(f"unsupported YAML frontmatter at line {line_number}")
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
    compatibility = fields.get("compatibility", "")
    negated_standalone = re.search(
        r"\b(?:not|never)\b[^.!?;]{0,40}\bstandalone\b", compatibility, re.IGNORECASE
    )
    if negated_standalone:
        result.append("frontmatter compatibility must not negate standalone")
    elif not re.search(r"\bstandalone\b", compatibility, re.IGNORECASE):
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

    identifiers: list[int] = []
    for index, eval_object in enumerate(evals):
        if not isinstance(eval_object, dict):
            errors.append(f"eval {index} must be a JSON object")
            continue
        missing = sorted(REQUIRED_EVAL_KEYS - eval_object.keys())
        if missing:
            errors.append(f"eval {index} is missing required keys: {', '.join(missing)}")
        identifier = eval_object.get("id")
        if isinstance(identifier, bool) or not isinstance(identifier, int):
            errors.append(f"eval {index} id must be an integer")
        elif identifier in identifiers:
            errors.append("eval IDs must be unique")
        else:
            identifiers.append(identifier)
        for field in EVAL_STRING_FIELDS:
            value = eval_object.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"eval {index} {field} must be a nonempty string")
        for field in EVAL_LIST_FIELDS:
            value = eval_object.get(field)
            valid = isinstance(value, list) and bool(value)
            if valid:
                valid = all(isinstance(item, str) and bool(item.strip()) for item in value)
            if not valid:
                errors.append(
                    f"eval {index} {field} must be a nonempty list of nonempty strings"
                )
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
    fixture_directory = root / "evals/files"
    try:
        fixture_root = fixture_directory.resolve()
    except (OSError, RuntimeError, ValueError):
        return ["eval fixture directory cannot be resolved"]
    if not _is_within(fixture_root, root):
        return ["eval fixture directory resolves outside repository"]
    if fixture_directory.is_symlink():
        return ["eval fixture directory must not be a symlink"]

    errors: list[str] = []
    for index, eval_object in enumerate(evals):
        if not isinstance(eval_object, dict):
            continue
        references = eval_object.get("files")
        if not isinstance(references, list):
            continue
        for reference in references:
            errors += _validate_fixture_reference(root, fixture_root, index, reference)
    return errors


def _validate_fixture_reference(
    root: Path, fixture_root: Path, index: int, reference: object
) -> list[str]:
    if not isinstance(reference, str) or not reference.strip():
        return [f"eval {index} fixture path must be a nonempty string"]
    if "\x00" in reference:
        return [f"eval {index} fixture path contains NUL"]
    reference_path = Path(reference)
    if reference_path.is_absolute():
        return [f"eval {index} fixture must stay under evals/files: {reference}"]
    try:
        candidate = (root / reference_path).resolve()
    except (OSError, RuntimeError, ValueError):
        return [f"eval {index} fixture cannot be resolved: {reference}"]
    if not _is_within(candidate, root):
        return [f"eval {index} fixture resolves outside repository: {reference}"]
    if not _is_within(candidate, fixture_root):
        return [f"eval {index} fixture must stay under evals/files: {reference}"]
    if not candidate.is_file():
        return [f"eval {index} fixture does not exist: {reference}"]
    return []


def _is_safe_publication_file(path: Path, root: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return _is_within(path.resolve(), root)
    except (OSError, RuntimeError, ValueError):
        return False


def _publication_files(root: Path) -> tuple[Path, ...]:
    files: set[Path] = set()
    for path in root.rglob("*"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDED_PUBLICATION_DIRS for part in relative.parts):
            continue
        if _is_safe_publication_file(path, root):
            files.add(path)
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
    if not target or target.startswith(("#", "//")):
        return None
    if URL_SCHEME.match(target) and not WINDOWS_ABSOLUTE_PATH.match(target):
        return None
    if "<" in target or ">" in target or "{" in target or "}" in target:
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0]) or None


def _validate_local_link(root: Path, source: Path, target: str) -> list[str]:
    display = _display_path(source, root)
    if "\x00" in target:
        return [f"local Markdown link contains NUL in {display}"]
    link_path = Path(target)
    if link_path.is_absolute() or WINDOWS_ABSOLUTE_PATH.match(target):
        return [f"local Markdown link must be relative in {display}: {target}"]
    if ".." in target.replace("\\", "/").split("/"):
        return [f"local Markdown link must not traverse directories in {display}: {target}"]
    try:
        candidate = (source.parent / link_path).resolve()
    except (OSError, RuntimeError, ValueError):
        return [f"local Markdown link cannot be resolved in {display}: {target}"]
    if not _is_within(candidate, root):
        return [f"local Markdown link resolves outside repository in {display}: {target}"]
    if not candidate.exists():
        return [f"broken local Markdown link in {display}: {target}"]
    return []


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
            if target is not None:
                errors += _validate_local_link(root, path, target)
    return errors


def _validate_forbidden_text(root: Path, files: tuple[Path, ...]) -> list[str]:
    errors: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_FILENAMES:
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


def _normalized_policy_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", " ")).lower()


def _dependency_negates_optionality(text: str, dependency: str) -> bool:
    normalized = _normalized_policy_text(text)
    escaped = re.escape(dependency.lower())
    clause = r"[^.!?;]{0,120}"
    return bool(
        re.search(rf"\b{escaped}\b{clause}\b(?:not|never)\s+optional\b", normalized)
        or re.search(rf"\b(?:not|never)\s+optional\b{clause}\b{escaped}\b", normalized)
    )


def _dependency_is_conditional(text: str, dependency: str) -> bool:
    normalized = _normalized_policy_text(text)
    escaped = re.escape(dependency.lower())
    clause = r"[^.!?;]{0,160}"
    patterns = (
        rf"\boptional\b{clause}\b{escaped}\b",
        rf"\b{escaped}\b{clause}\boptional\b",
        rf"\b{escaped}\b{clause}\b(?:can|may)\s+enhance\b",
        rf"\b(?:if|when)\b{clause}\b{escaped}\b{clause}\bavailable\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


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
        if _dependency_negates_optionality(combined, dependency):
            errors.append(f"dependency {dependency!r} must not negate optionality")
        elif not _dependency_is_conditional(combined, dependency):
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
