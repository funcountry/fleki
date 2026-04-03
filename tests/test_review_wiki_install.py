from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.install_knowledge_skill import (
    REPO_ROOT,
    QUARTZ_PACKAGE_REFERENCE,
    QUARTZ_VERSION,
    QUARTZ_NPM_MIN_VERSION,
    QUARTZ_REQUIRED_NODE_MAJOR,
    build_parser,
    ensure_review_wiki_tooling,
    materialize_quartz_runtime_scaffold,
    materialize_review_wiki_overlay,
    port_existing_graph_frontmatter,
)


class ReviewWikiInstallTest(unittest.TestCase):
    def test_parser_accepts_review_wiki_flags(self) -> None:
        parser = build_parser()

        install_args = parser.parse_args(["--review-wiki"])
        remove_args = parser.parse_args(["--remove-review-wiki"])

        self.assertTrue(install_args.review_wiki)
        self.assertFalse(install_args.remove_review_wiki)
        self.assertTrue(remove_args.remove_review_wiki)
        self.assertFalse(remove_args.review_wiki)

    def test_review_wiki_tooling_preflight_accepts_required_versions(self) -> None:
        responses = {
            ("node", "--version"): f"v{QUARTZ_REQUIRED_NODE_MAJOR}.1.0",
            ("npm", "--version"): QUARTZ_NPM_MIN_VERSION,
        }

        with mock.patch("scripts.install_knowledge_skill.shutil.which") as which_mock:
            which_mock.side_effect = lambda name: f"/usr/local/bin/{name}"
            tooling = ensure_review_wiki_tooling(
                runner=lambda command: responses[tuple(command)],
            )

        self.assertEqual(tooling["uv_path"], Path("/usr/local/bin/uv"))

    def test_review_wiki_tooling_preflight_rejects_old_node(self) -> None:
        responses = {
            ("node", "--version"): "v21.9.0",
            ("npm", "--version"): QUARTZ_NPM_MIN_VERSION,
        }

        with mock.patch("scripts.install_knowledge_skill.shutil.which") as which_mock:
            which_mock.side_effect = lambda name: f"/usr/local/bin/{name}"
            with self.assertRaises(SystemExit) as exit_info:
                ensure_review_wiki_tooling(runner=lambda command: responses[tuple(command)])

        self.assertIn("review wiki requires Node >=", str(exit_info.exception))

    def test_review_wiki_overlay_copy_preserves_non_template_state(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        template_root = root / "template"
        quartz_root = root / "quartz"
        template_root.mkdir(parents=True, exist_ok=True)
        quartz_root.mkdir(parents=True, exist_ok=True)

        for name in ("README.md", "package.json", "quartz.config.ts", "quartz.layout.ts", "tsconfig.json"):
            (template_root / name).write_text(f"{name}\n")
        (quartz_root / "node_modules").mkdir()
        (quartz_root / "node_modules" / "keep.txt").write_text("ok\n")

        materialize_review_wiki_overlay(template_root, quartz_root)

        self.assertTrue((quartz_root / "package.json").exists())
        self.assertTrue((quartz_root / "node_modules" / "keep.txt").exists())

    def test_review_wiki_template_pins_quartz_tarball_reference(self) -> None:
        package_json_path = REPO_ROOT / "templates" / "review-wiki" / "package.json"

        package_json = json.loads(package_json_path.read_text())

        self.assertEqual(
            package_json["dependencies"]["@jackyzha0/quartz"],
            QUARTZ_PACKAGE_REFERENCE,
        )
        self.assertEqual(package_json["version"], QUARTZ_VERSION)
        self.assertEqual(
            QUARTZ_PACKAGE_REFERENCE,
            f"https://codeload.github.com/jackyzha0/quartz/tar.gz/refs/tags/v{QUARTZ_VERSION}",
        )

    def test_quartz_template_imports_local_scaffold(self) -> None:
        config_text = (REPO_ROOT / "templates" / "review-wiki" / "quartz.config.ts").read_text()
        layout_text = (REPO_ROOT / "templates" / "review-wiki" / "quartz.layout.ts").read_text()

        self.assertIn('from "./quartz/cfg"', config_text)
        self.assertIn('from "./quartz/plugins"', config_text)
        self.assertIn('from "./quartz/cfg"', layout_text)
        self.assertIn('from "./quartz/components"', layout_text)

    def test_materialize_quartz_runtime_scaffold_copies_installed_quartz_dir(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        quartz_root = Path(temp_dir.name) / "quartz"
        installed_scaffold = quartz_root / "node_modules" / "@jackyzha0" / "quartz" / "quartz"
        installed_scaffold.mkdir(parents=True, exist_ok=True)
        (installed_scaffold / "build.ts").write_text("export {}\n")

        materialize_quartz_runtime_scaffold(quartz_root)

        self.assertEqual((quartz_root / "quartz" / "build.ts").read_text(), "export {}\n")

    def test_installer_ports_existing_graph_frontmatter_explicitly(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        data_root = root / "data-root"
        topic_path = data_root / "topics" / "product" / "legacy.md"
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text(
            "---\n"
            "{\n"
            "  \"knowledge_id\": \"kg_legacy\",\n"
            "  \"current_path\": \"product/legacy\",\n"
            "  \"page_kind\": \"topic\"\n"
            "}\n"
            "---\n"
            "# Legacy Topic\n"
        )

        class Layout:
            def __init__(self, data_root: Path) -> None:
                self.data_root = data_root

        ported_files = port_existing_graph_frontmatter(Layout(data_root))

        self.assertEqual(ported_files, 1)
        self.assertNotIn("{", topic_path.read_text().split("---", 2)[1])


if __name__ == "__main__":
    unittest.main()
