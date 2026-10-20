# Katachi (形)

*See the shape your tree could become.*

> **Status: early development (v0.1 in progress).** Nothing here is usable yet.

Katachi is an open source tool for bonsai hobbyists. Upload a photo of your tree to see its
species profile and bonsai care notes, then preview it restyled as **Informal upright (Moyogi)**,
**Slanting (Shakan)**, or **Windswept (Fukinagashi)**, with a before/after slider.

<!-- TODO: before/after GIF and hosted demo link go here. -->

## Planned features (v0.1)

- Photo upload with built-in sample photos and friendly validation
- Automatic background removal (tree and pot)
- Tree Profile card: predicted species with confidence, care practices, suitable styles, and a
  rough structure estimate, with a manual species override
- AI restyle that keeps your pot, background, and tree identity, with regenerate and download

Previews show a *possible* future shape, not a guarantee. Real styling takes years.

## Quick start (development)

Requires Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check .
```

Full instructions (Docker, GPU/CPU notes, Hugging Face Space) arrive with the v0.1 release.

## Contributing

Species data and style templates are the easiest places to help. Contribution guides are coming
soon in `CONTRIBUTING.md` and `docs/`.

## License

Apache-2.0 (pending owner confirmation). See [LICENSE](LICENSE). Third-party models and their
licenses are listed in [MODEL_LICENSES.md](MODEL_LICENSES.md).
