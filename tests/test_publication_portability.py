from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
READMES = (
    {
        "path": "README.md",
        "agent_label": r"AI[- ]agent",
        "copy_paste": r"\bcopy\b.*\bpaste\b",
        "identity": "portable AI-agent skill",
        "manual_heading": "## Manual installation",
        "required_prompt_fragments": (
            "supports reusable skill.md skills",
            "v0.1.1 or newer",
            "exact release tag",
            "commit sha",
            "install scope",
            "target path",
            "ask me to approve",
            "before writing",
            "do not install from main",
            "sha-256",
            "paper-study/skill.md",
            "paper-study/references/note-template.md",
            "regular files",
            "path traversal",
            "symlinks",
            "before replacing",
            "restart or reload",
            "does not support skill.md skills",
            "custom-instruction or workspace setup",
        ),
        "manual_safety": (
            "do not merge-copy into an existing directory",
            "before replacing it",
        ),
        "provider_only": r"(?:exclusively|only)\s+(?:an?\s+)?(?:Claude|GPT|OpenAI|Gemini|Codex)",
    },
    {
        "path": "README.zh-CN.md",
        "agent_label": r"AI\s*(?:编程)?智能体",
        "copy_paste": r"复制.*粘贴",
        "identity": "可移植的 AI 智能体技能",
        "manual_heading": "## 手动安装",
        "required_prompt_fragments": (
            "支持可复用的 skill.md 技能",
            "v0.1.1 或更高版本",
            "准确的 release 标签",
            "提交 sha",
            "安装范围",
            "目标路径",
            "请我确认",
            "写入前",
            "不要从 main 安装",
            "sha-256",
            "paper-study/skill.md",
            "paper-study/references/note-template.md",
            "普通文件",
            "路径穿越",
            "符号链接",
            "覆盖前",
            "重启或重新加载",
            "不支持 skill.md 技能",
            "自定义指令或项目工作区配置",
        ),
        "manual_safety": (
            "不要合并复制到已有目录",
            "覆盖前",
        ),
        "provider_only": r"(?:仅|只)\s*(?:是|用于|支持)?\s*(?:Claude|GPT|OpenAI|Gemini|Codex)",
    },
)
SKILL_PATH = REPO_ROOT / "skill" / "paper-study" / "SKILL.md"
OPTIONAL_MEMORY_POLICY = (
    "Persistent memory is optional. Use it only when the host provides it and the reader has "
    "explicitly opted in. If either condition is absent, do not read from or write study context "
    "to memory; the note and route table remain the complete resumption state."
)
MEMORY_POLICY_MARKER = "optional-memory policy permits"
HOST_MEMORY_REFERENCE = re.compile(
    r"\b(?:persistent|host(?:-provided)?|optional\s+host)\s+memory\b",
    re.IGNORECASE,
)


class PublicationPortabilityTestCase(unittest.TestCase):
    def _after_language_link(self, text: str) -> str:
        lines = text.splitlines()
        self.assertRegex(lines[0], r"^#\s+\S")
        language_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip()
        )
        self.assertRegex(lines[language_index], r"^\[[^]]+\]\([^)]+\)$")
        return "\n".join(lines[language_index + 1 :]).lstrip()

    def _leading_install_section(self, text: str) -> str:
        opening = self._after_language_link(text)
        headings = list(re.finditer(r"^##(?:\s|$)", opening, re.MULTILINE))
        self.assertGreaterEqual(len(headings), 2)
        self.assertEqual(headings[0].start(), 0)
        return opening[: headings[1].start()]

    def _section(self, text: str, heading: str) -> str:
        start = text.index(heading)
        remainder = text[start + len(heading) :]
        match = re.search(r"^##(?:\s|$)", remainder, re.MULTILINE)
        return remainder[: match.start()] if match else remainder

    def test_readmes_lead_with_complete_provider_neutral_install_prompt(self) -> None:
        named_providers = re.compile(
            r"(?:Anthropic|Claude|OpenAI|GPT|Gemini|Codex)",
            re.IGNORECASE,
        )
        for case in READMES:
            with self.subTest(relative=case["path"]):
                text = (REPO_ROOT / case["path"]).read_text(encoding="utf-8")
                install_section = self._leading_install_section(text)
                first_line = install_section.splitlines()[0]
                self.assertRegex(first_line, rf"^##+\s+.*{case['agent_label']}")
                self.assertRegex(install_section, re.compile(case["copy_paste"], re.DOTALL | re.IGNORECASE))

                prompt_match = re.search(
                    r"```(?:text|markdown|prompt)?\s*\n(?P<body>.*?)\n```",
                    install_section,
                    re.DOTALL | re.IGNORECASE,
                )
                self.assertIsNotNone(prompt_match, "installation prompt must be copy-pasteable")
                prompt = prompt_match.group("body") if prompt_match is not None else ""
                prompt_casefolded = prompt.casefold()
                for fragment in case["required_prompt_fragments"]:
                    self.assertIn(fragment.casefold(), prompt_casefolded)
                self.assertIsNone(named_providers.search(prompt))
                self.assertNotIn(".claude", install_section.casefold())

    def test_readmes_do_not_use_disallowed_prompt_labels(self) -> None:
        forbidden = {"README.md": "foolproof", "README.zh-CN.md": "傻瓜式"}
        for relative, label in forbidden.items():
            with self.subTest(relative=relative):
                text = (REPO_ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn(label.casefold(), text.casefold())

    def test_readme_product_identity_is_provider_neutral(self) -> None:
        for case in READMES:
            with self.subTest(relative=case["path"]):
                text = (REPO_ROOT / case["path"]).read_text(encoding="utf-8")
                self.assertIn(case["identity"].casefold(), text.casefold())
                self.assertNotRegex(text, re.compile(case["provider_only"], re.IGNORECASE))
                self.assertNotRegex(text, re.compile(r"`?paper-study`?\s+is\s+(?:an?\s+)?Claude\s+skill", re.IGNORECASE))

    def test_manual_installation_does_not_merge_existing_targets(self) -> None:
        for case in READMES:
            with self.subTest(relative=case["path"]):
                text = (REPO_ROOT / case["path"]).read_text(encoding="utf-8")
                section = self._section(text, case["manual_heading"])
                self.assertNotRegex(section, re.compile(r"```(?:ba)?sh|\bcp\s+-R\b", re.IGNORECASE))
                for fragment in case["manual_safety"]:
                    self.assertIn(fragment.casefold(), section.casefold())

    def test_core_skill_does_not_require_named_host_api(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertNotIn("AskUserQuestion", skill)
        self.assertNotIn(".claude", skill.casefold())
        self.assertNotRegex(skill, r"(?i)\bClaude(?:-only)?\s+skill\b")

    def test_persistent_memory_uses_one_explicit_opt_in_policy(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        _, _, body = skill.split("---", 2)
        normalized_body = " ".join(body.split())
        self.assertEqual(normalized_body.count(OPTIONAL_MEMORY_POLICY), 1)

        memory_blocks = [
            block
            for block in re.split(r"\n\s*\n", body)
            if HOST_MEMORY_REFERENCE.search(block)
        ]
        self.assertTrue(memory_blocks, "expected host-memory references in SKILL.md")
        unbound = [
            " ".join(block.split())[:180]
            for block in memory_blocks
            if OPTIONAL_MEMORY_POLICY not in " ".join(block.split())
            and MEMORY_POLICY_MARKER not in block.casefold()
        ]
        self.assertEqual(unbound, [], "host-memory reference not bound to the optional-memory policy")


if __name__ == "__main__":
    unittest.main()
