# Fleki Knowledge

This repo owns the `knowledge` skill, its bundled Python runtime, and the
on-disk knowledge graph format.

Install it from this checkout with one command:

```bash
./install.sh
```

Requirements:

- `uv`
- `npx` if Codex is installed on the machine

What `./install.sh` does:

- regenerates `skills/knowledge/runtime/**`
- installs the bundled `knowledge` CLI with PDF support through `docling`
- installs Codex into `~/.agents/skills/knowledge` through the upstream `npx skills add` flow when Codex is present
- copies the skill into every detected Hermes home at `<hermes-home>/skills/knowledge`
- copies the skill into every detected OpenClaw root at `<openclaw-root>/skills/knowledge`
- writes or refreshes the install manifest at the platform-standard Fleki config path

Preview detected targets without writing anything:

```bash
./install.sh --dry-run
```

Limit install to one or more runtimes:

```bash
./install.sh --surface codex --surface hermes
```

Quick smoke after install:

```bash
knowledge status --json --no-receipt
```

The canonical mutable graph data does not live in this repo checkout and does
not live in runtime skill directories. On this host it resolves to:

```text
~/.fleki/knowledge
```

Use `knowledge status` on any machine to confirm the real path.

Installing or refreshing the CLI is not the same thing as starting with an
empty graph. A fresh install can attach to an already populated shared graph
under `~/.fleki/knowledge`.

## Naming Crosswalk

- Distribution package: `fleki-knowledge-graph`
- Python module: `knowledge_graph`
- CLI: `knowledge`
- Skill key: `fleki/knowledge`

## Save Contract Notes

- Each binding object may include `timestamp` as ISO 8601 source-observed time.
- `knowledge_units[].temporal_scope` accepts:
  - `evergreen`
  - `time_bound`
  - `ephemeral`
- `topic_actions[].lifecycle_state` in `knowledge save` accepts:
  - `current`
  - `historical`
- `knowledge rebuild` owns `stale` and delete.
- `source_kind` stays tolerant in code. Routing is normalized like this:
  - `pdf*` or `.pdf` -> `sources/pdf/`
  - `image*` or common image suffixes -> `sources/images/`
  - `codex*`, `paperclip*`, `hermes*` -> matching source family
  - everything else, including markdown/text, -> `sources/other/`

If you already have an older Fleki install under `~/Library/Application Support/Fleki`
or `~/.config/fleki`, rerunning `./install.sh` migrates it into `~/.fleki` and
removes the old root after verification succeeds.

## Canonical Paths

- `skills/knowledge/**` is the human-edited skill package.
- `skills/knowledge/runtime/**` is the generated bundled runtime.
- `knowledge/**` is the canonical graph data when you are working inside a test repo fixture. Production installs use the machine-level data root instead.

## Manual PDF Smoke

After `./install.sh`, run this exact smoke from the repo root:

```bash
tmp_dir="$(mktemp -d)"
cp docs/phase6_smoke_inputs/knowledge_pdf_input.pdf "$tmp_dir/input.pdf"

cat > "$tmp_dir/bindings.json" <<JSON
[
  {
    "source_id": "pdf.readme.smoke",
    "local_path": "$tmp_dir/input.pdf",
    "source_kind": "pdf_research",
    "authority_tier": "historical_support",
    "sensitivity": "internal",
    "preserve_mode": "copy",
    "timestamp": "2026-04-03T12:00:00+00:00"
  }
]
JSON

cat > "$tmp_dir/decision.json" <<'JSON'
{
  "ingest_summary": {
    "source_ids": ["pdf.readme.smoke"],
    "primary_domains": ["product"],
    "authority_tier": "historical_support",
    "sensitivity": "internal",
    "semantic_summary": "README smoke for bundled PDF support."
  },
  "source_reading_reports": [
    {
      "source_id": "pdf.readme.smoke",
      "reading_mode": "direct_local_pdf",
      "approved_helpers_used": [],
      "readable_units": ["full text"],
      "gaps": [],
      "confidence_notes": []
    }
  ],
  "topic_actions": [
    {
      "topic_path": "product/readme/pdf-smoke",
      "page_kind": "topic",
      "action": "create",
      "lifecycle_state": "current",
      "candidate_title": "README PDF Smoke",
      "why": "Manual smoke for the installed PDF path.",
      "knowledge_units": [
        {
          "kind": "principle",
          "temporal_scope": "time_bound",
          "target_section": {
            "section_id": null,
            "heading": "Current Understanding"
          },
          "statement": "README PDF smoke succeeded.",
          "rationale": "The installed skill could render and ingest the fixture PDF.",
          "authority_posture": "supported_by_internal_session",
          "confidence": "high",
          "evidence": [
            {
              "source_id": "pdf.readme.smoke",
              "locator": "manual smoke",
              "notes": ""
            }
          ]
        }
      ]
    }
  ],
  "provenance_notes": [
    {
      "source_ids": ["pdf.readme.smoke"],
      "bundle_rationale": null,
      "title": "README PDF smoke provenance",
      "summary": "Fixture PDF used to confirm bundled PDF support.",
      "source_reading_summary": "Read directly from the local filesystem.",
      "what_this_source_contributes": ["Proof that PDF rendering worked."],
      "knowledge_sections_touched": [
        {
          "topic_path": "product/readme/pdf-smoke",
          "section_heading": "Current Understanding"
        }
      ],
      "sensitivity_notes": "internal"
    }
  ],
  "conflicts_or_questions": [],
  "asset_actions": [],
  "recommended_next_step": {
    "action": "queue_rebuild_topic",
    "scope": ["product"],
    "why": "Refresh semantic neighbors later if needed."
  }
}
JSON

knowledge save --json --bindings "$tmp_dir/bindings.json" --decision "$tmp_dir/decision.json"
```

That smoke should create a PDF render markdown and render manifest under the
resolved machine data root in `sources/pdf/`.
