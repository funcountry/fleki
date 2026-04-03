# Install And Repair

This skill is self-contained.

From a Fleki repo checkout, use the repo entrypoint:

```bash
./install.sh
```

That command:

- regenerates `skills/knowledge/runtime/**`
- installs the bundled `knowledge` CLI with PDF support
- installs the skill into each detected runtime's native location
- refreshes the machine install manifest and centralized `~/.fleki` knowledge-home layout
- migrates older Fleki installs from `~/Library/Application Support/Fleki` or `~/.config/fleki` into `~/.fleki`

Installing or repairing the CLI does not clear an existing graph. A fresh
install can still point at an already populated shared root under
`~/.fleki/knowledge`.

If you already have this skill bundle on disk and only need to repair the CLI
and manifest from the bundle itself:

```bash
bash install/bootstrap.sh
```

That bundle-native repair path does not depend on a Fleki repo checkout.
