from __future__ import annotations

import unittest

from knowledge_graph.frontmatter import (
    dump_frontmatter,
    split_frontmatter,
    split_frontmatter_for_migration,
)


class FrontmatterCodecTest(unittest.TestCase):
    def test_yaml_round_trip_preserves_timestamp_strings(self) -> None:
        metadata = {
            "aliases": [],
            "created_at": "2026-04-03T03:40:53+00:00",
            "nested": {"last_updated_at": "2026-04-03T03:53:37+00:00"},
        }

        rendered = dump_frontmatter(metadata, "# Topic\n")
        parsed_metadata, body = split_frontmatter(rendered)

        self.assertEqual(parsed_metadata, metadata)
        self.assertEqual(body, "# Topic\n")
        self.assertIsInstance(parsed_metadata["created_at"], str)
        self.assertIsInstance(parsed_metadata["nested"]["last_updated_at"], str)

    def test_canonical_parser_rejects_legacy_json_frontmatter(self) -> None:
        text = "---\n{\n  \"created_at\": \"2026-04-03T03:40:53+00:00\"\n}\n---\n# Topic\n"

        with self.assertRaises(ValueError):
            split_frontmatter(text)

    def test_migration_parser_reads_legacy_json_frontmatter(self) -> None:
        text = "---\n{\n  \"created_at\": \"2026-04-03T03:40:53+00:00\"\n}\n---\n# Topic\n"

        metadata, body = split_frontmatter_for_migration(text)

        self.assertEqual(metadata, {"created_at": "2026-04-03T03:40:53+00:00"})
        self.assertEqual(body, "# Topic\n")


if __name__ == "__main__":
    unittest.main()
