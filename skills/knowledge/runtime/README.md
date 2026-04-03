# Fleki Knowledge Runtime

This directory is the generated Python runtime that ships inside the `knowledge` skill.
It lets the installed skill install and refresh the `knowledge` CLI without depending on a Fleki repo checkout.

Naming crosswalk:
- distribution package: `fleki-knowledge-graph`
- Python module: `knowledge_graph`
- CLI: `knowledge`
- skill key: `fleki/knowledge`

Persistent-root note:
- installing or refreshing the CLI does not clear an existing graph
- the shared graph root resolves under `~/.fleki/knowledge` unless an install manifest says otherwise

Save contract notes:
- bindings may include `timestamp` as ISO 8601 source-observed time
- `knowledge_units[].temporal_scope`: `evergreen`, `time_bound`, `ephemeral`
- `topic_actions[].lifecycle_state`: `current` or `historical`
- `knowledge rebuild` owns `stale` and delete

Minimal valid save example:

Create `bindings.json`:

```json
[
  {
    "source_id": "note.customerio.current",
    "local_path": "/absolute/path/to/customer-io.md",
    "source_kind": "markdown_doc",
    "authority_tier": "live_doctrine",
    "timestamp": "2026-04-03T12:00:00+00:00"
  }
]
```

Create `decision.json`:

```json
{
  "ingest_summary": {
    "source_ids": ["note.customerio.current"],
    "primary_domains": ["product"],
    "authority_tier": "live_doctrine",
    "sensitivity": "internal",
    "semantic_summary": "Customer.io setup guidance."
  },
  "source_reading_reports": [
    {
      "source_id": "note.customerio.current",
      "reading_mode": "direct_local_text",
      "approved_helpers_used": [],
      "readable_units": ["full text"],
      "gaps": [],
      "confidence_notes": []
    }
  ],
  "topic_actions": [
    {
      "topic_path": "product/customer-io/current-setup",
      "page_kind": "topic",
      "action": "create",
      "lifecycle_state": "current",
      "candidate_title": "Customer.io Current Setup",
      "why": "Capture the current setup guidance.",
      "knowledge_units": [
        {
          "kind": "fact",
          "temporal_scope": "time_bound",
          "target_section": {
            "section_id": null,
            "heading": "Current Understanding"
          },
          "statement": "Customer.io is configured through the current workspace flow.",
          "rationale": "This source describes the current setup path.",
          "authority_posture": "live_doctrine",
          "confidence": "high",
          "evidence": [
            {
              "source_id": "note.customerio.current",
              "locator": "entire note",
              "notes": ""
            }
          ]
        }
      ]
    }
  ],
  "provenance_notes": [
    {
      "source_ids": ["note.customerio.current"],
      "bundle_rationale": null,
      "title": "Customer.io setup provenance",
      "summary": "Current setup guidance from the local source.",
      "source_reading_summary": "Read directly from the local filesystem.",
      "what_this_source_contributes": ["Current Customer.io setup guidance."],
      "knowledge_sections_touched": [
        {
          "topic_path": "product/customer-io/current-setup",
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
    "scope": ["product/customer-io"],
    "why": "Refresh nearby semantic neighbors later if needed."
  }
}
```

Apply it with:

```bash
knowledge save --bindings bindings.json --decision decision.json
```

Included behavior:
- `knowledge status`
- `knowledge search`
- `knowledge trace`
- `knowledge save`
- `knowledge rebuild`
- bundled PDF render support through `docling`

Install the CLI from this directory:

```bash
uv tool install --force .
```

This directory is generated. Edit `src/knowledge_graph/**`, `pyproject.toml`, or `skills/knowledge/**` in Fleki, then regenerate the runtime bundle.
