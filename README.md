# Katachi (形)

> **Status: early development (v0.1 in progress).** Nothing here is usable yet.

Katachi is an open source tool for bonsai hobbyists. Upload a photo of your tree to see its
species, sourced bonsai care practices, and which styles (**Informal upright (Moyogi)**,
**Slanting (Shakan)**, **Windswept (Fukinagashi)**) suit it.

<!-- TODO: screenshot and hosted demo link go here. -->

## Planned features (v0.1)

- Photo upload with built-in sample photos and friendly validation
- Automatic background removal (tree and pot)
- Tree Profile card: predicted species with confidence, care practices from sourced species
  files, suitable styles, and a rough structure estimate, with a manual species override

## Quick start (development)

Requires Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[segment,dev]"
pytest && ruff check .
python -m katachi.pipeline --image path/to/tree.jpg   # saves the isolated tree + pot
```

Background removal downloads the U2-Net model (~170 MB) on first use.

## Contributing

Species data is the easiest place to help. Contribution guides are coming soon in
`CONTRIBUTING.md` and `docs/`.

## License

Apache-2.0. See [LICENSE](LICENSE). Third-party models and their licenses are listed in
[MODEL_LICENSES.md](MODEL_LICENSES.md).
