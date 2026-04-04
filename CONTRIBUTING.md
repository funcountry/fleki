# Contributing

Thanks for contributing to Fleki.

## Before you change code

- Use `.venv/bin/python`. The repo expects Python 3.12.
- Install or refresh the local environment first if needed:

```bash
./install.sh
```

## Repo layout

- `src/knowledge_graph/**` is the Python source of truth.
- `tests/**` is the automated coverage.
- `skills/knowledge/**` is the human-edited skill source.
- `skills/knowledge/runtime/**` is generated. Do not hand-edit it.
- `knowledge/**` is reference content and a migration seed, not the live mutable graph.

If you change runtime-facing behavior, update the owning docs in the same change.

## Verification

Run the smallest relevant check while you work:

```bash
PYTHONPATH=src:tests .venv/bin/python -m unittest tests.test_<module> -v
```

Run the full suite before you open or update a pull request for changes under
`src/knowledge_graph/**`, `tests/**`, or install and publish code:

```bash
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m compileall src
```

If you change the generated runtime owner under `src/knowledge_graph/**`,
refresh the runtime bundle too:

```bash
.venv/bin/python scripts/sync_knowledge_runtime.py
```

## Pull requests

- Keep one clear owner per rule or implementation. Do not leave old and new paths alive together.
- Delete replaced code and docs in the same change.
- Include the concrete behavior change, the commands you ran, and any remaining gap in the pull request description.

## License

By contributing to this repository, you agree that your contributions are
licensed under the MIT License in [LICENSE](LICENSE).
