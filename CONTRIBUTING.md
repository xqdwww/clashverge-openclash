# Contributing

Keep the project within its local conversion boundary. Changes must not add
subscription fetching, health probing, router access, SSH, remote commands,
deployment, OpenClash process control, or private environment integration.

Use only synthetic fixtures with RFC 5737 TEST-NET addresses and explicit fake
credentials. Never commit a real configuration or audit artifact.

Run the release gates before proposing a change:

```bash
python -m pip install -e ".[dev]"
ruff check .
python -m compileall -q src tests
python -m pytest
```

New supported configuration fields must cite a public format document, define
validation and failure behavior, and include focused tests. Do not copy or
translate implementation code from upstream or private tools.
