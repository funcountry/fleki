# Fleki Knowledge

Fleki Knowledge is a local-first semantic knowledge graph runtime for agent workflows.

It gives you a `knowledge` CLI plus packaged skill installs for Codex, Hermes, and OpenClaw, so the same graph can be searched, traced, saved, and rebuilt across multiple agent runtimes.

## Why use it

- Search semantic knowledge pages instead of dumping raw files into a folder.
- Trace claims back to source records, provenance notes, and PDF render artifacts.
- Work with local markdown, images, and PDFs.
- Keep the graph inspectable on disk under a normal directory tree.
- Use one install flow to provision the CLI and the runtime-specific skill bundles.

## What it does

The `knowledge` CLI supports five core workflows:

| Command | Purpose |
| --- | --- |
| `knowledge status` | Inspect the active graph root and rebuild backlog. |
| `knowledge search` | Search semantic pages. |
| `knowledge trace` | Follow a page or claim back to provenance and source records. |
| `knowledge save` | Commit a semantic ingestion decision with provenance. |
| `knowledge rebuild` | Apply page moves, lifecycle updates, and cleanup after larger changes. |

## Install

Install from this checkout with:

```bash
./install.sh
```

Requirements:

- `uv`
- `npx` if Codex is installed on the machine
- Node `>=22` and npm `>=10.9.2` if you want the optional review wiki

Useful install variants:

```bash
./install.sh --dry-run
./install.sh --surface codex
./install.sh --surface hermes --surface openclaw
```

What `./install.sh` does:

- regenerates the bundled runtime under `skills/knowledge/runtime/**`
- installs the `knowledge` CLI with PDF support through `docling`
- installs or refreshes the Codex skill when Codex is present
- copies the skill into each detected Hermes home
- copies the skill into each detected OpenClaw root
- writes or refreshes the install manifest under `$HOME/.fleki`

Install the optional local review wiki on this machine:

```bash
./install.sh --review-wiki
```

That installs the normal Fleki runtime pieces, then installs a per-user review
wiki service on macOS or Linux. The site serves locally at:

```text
http://127.0.0.1:4151
```

The review wiki exports only `topics/**`, `topics/indexes/**`, and
`provenance/**` into derived state under `~/.fleki/state/review-wiki`. It does
not publish `sources/**`, `receipts/**`, or raw record JSON.

Remove the review wiki later with:

```bash
./install.sh --remove-review-wiki
```

Quick smoke after install:

```bash
knowledge status --json --no-receipt
```

Look for these fields in the output:

- `resolved_data_root`
- `install_manifest_path`
- `recent_topics`
- `pdf_render_contract_gap_count`

## Quick start

Check the active graph:

```bash
knowledge status --json --no-receipt
```

Search what is already known:

```bash
knowledge search "customer.io"
```

If nothing matches, `knowledge search` returns zero results. It should not invent a nearest answer.

Trace a topic back to its sources:

```bash
knowledge trace product/customer-io/current-setup --json --no-receipt
```

Best-effort claim text trace is stricter than path trace. It should only return a result when it can narrow to a real section and evidence.

Commit a save from local files:

```bash
knowledge save --bindings bindings.json --decision decision.json --json
```

Apply a rebuild plan:

```bash
knowledge rebuild --plan rebuild.json --json
```

## Save workflow

`knowledge save` is the semantic write step.
It applies immediately. There is no preview, validate-only, or dry-run save path.

For a minimal valid save payload, start from the checked-in example templates:

- [skills/knowledge/references/examples/minimal-save-bindings.json](skills/knowledge/references/examples/minimal-save-bindings.json)
- [skills/knowledge/references/examples/minimal-save-decision.json](skills/knowledge/references/examples/minimal-save-decision.json)

A few usage-critical rules:

- Use `fact` for plain observations unless another kind adds stronger semantic meaning.
- `ingest_summary.authority_tier` and `knowledge_units[].authority_posture` are different enums. Do not swap them.
- `timestamp` is optional and records source-observed time.
- `knowledge rebuild` owns `stale` and delete.

For the full save contract, see [skills/knowledge/references/save-ingestion.md](skills/knowledge/references/save-ingestion.md).

## How data is stored

The canonical mutable graph is not stored in this repo checkout. By default it lives under:

```text
$HOME/.fleki/knowledge
```

Installing or refreshing the CLI does not clear that graph. A fresh install can still attach to an already populated shared root.

The on-disk layout is simple:

- `topics/` holds semantic pages
- `provenance/` holds source-backed notes
- `sources/` holds copied files or durable pointers
- `receipts/` holds command receipts

Copied PDFs also persist a source-adjacent render bundle:

- `.render.md`
- `.render.manifest.json`
- optional `.assets/`

If an older PDF source record predates that render contract, `knowledge trace` surfaces the gap and `knowledge status` reports it through `pdf_render_contract_gap_count`.

## Runtime integrations

This project is designed to work across multiple agent runtimes while keeping one shared graph.

- Codex: installs the skill under `~/.agents/skills/knowledge`
- Hermes: copies the skill into each detected Hermes home
- OpenClaw: copies the skill into each detected OpenClaw root

The standalone CLI is still useful on its own. The integrations mainly ensure those runtimes can use the same `knowledge` workflow and shared data root.

## Maintenance and troubleshooting

If something looks wrong, start here:

```bash
knowledge status --json --no-receipt
```

Common fixes:

- Repair an installed bundle from the bundle itself:

  ```bash
  bash skills/knowledge/install/bootstrap.sh
  ```

- Backfill older PDF source records that predate the render-or-omission contract:

  ```bash
  .venv/bin/python scripts/backfill_pdf_render_contract.py --json
  ```

Notes:

- A non-empty graph after install is expected if `$HOME/.fleki/knowledge` already existed.

## Repo map

If you are working in this repo directly:

- `src/knowledge_graph/**` is the Python implementation
- `skills/knowledge/**` is the human-edited skill package
- `skills/knowledge/runtime/**` is the generated bundled runtime
- `knowledge/README.md` describes the on-disk graph tree

## Learn more

- [skills/knowledge/install/README.md](skills/knowledge/install/README.md)
- [skills/knowledge/references/save-ingestion.md](skills/knowledge/references/save-ingestion.md)
- [skills/knowledge/references/search-and-trace.md](skills/knowledge/references/search-and-trace.md)
- [skills/knowledge/references/examples-and-validation.md](skills/knowledge/references/examples-and-validation.md)
- [knowledge/README.md](knowledge/README.md)
