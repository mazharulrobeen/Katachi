# Katachi (形): Project Spec and Build Instructions

> Put this file in the root of the repo as `CLAUDE.md`. Claude Code reads it automatically at the start of every session.

## 1. Project overview

**Katachi** is an open source tool where a user uploads a photo of their bonsai tree and sees details about the tree: species, scientific name, bonsai care practices, suitable styles, and rough structure.

> **Scope change (2026-10-20):** the owner dropped the AI restyle feature (Stable Diffusion img2img + ControlNet) to avoid multi-GB local model downloads. Do **not** reintroduce image generation without asking the owner. The removed code is in git history (commit `5b824ad`).

- **Tagline:** *TODO: owner to choose a new tagline (the old one, "See the shape your tree could become", described the dropped restyle preview).*
- **Owner / GitHub org:** Engramium
- **Repo name:** `katachi`
- **Name meaning:** 形 (katachi) is Japanese for "shape" or "form".
- **Current target:** **v0.1, the first public release** (scope below).

### Why this project exists
Its main goals are real usefulness to bonsai hobbyists and an easy path for open source contributors (species data). Optimize for: **a polished, narrow v0.1 that works reliably** over a broad, half-working one.

---

## 2. v0.1 goal

A stranger opens the hosted demo, picks a sample bonsai photo (or uploads their own), and sees an accurate, sourced **Tree Profile** in a few seconds.

---

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| UI | **Gradio** | Deploys directly to Hugging Face Spaces |
| Background removal | `rembg` (U2-Net) as default; SAM as optional upgrade | Keep behind an interface so models are swappable |
| Species identification | Pluggable provider interface | Default: Pl@ntNet API (free tier) or a vision-language model API; must work with a manual override |
| Species data | YAML files in `species/` | Validated with a schema (pydantic) |
| Tests | `pytest` | |
| Packaging | `pyproject.toml`, `Dockerfile`, `docker-compose.yml` | One-command local run |
| Lint / format | `ruff` | |

If a choice here causes a real problem (license, performance, availability), stop and propose an alternative instead of silently switching.

---

## 4. Repository structure

```
katachi/
├── CLAUDE.md                  # this file
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── MODEL_LICENSES.md          # table of every model/weight used and its license
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── app.py                     # Gradio entry point
├── src/katachi/
│   ├── __init__.py
│   ├── config.py              # settings, env vars, model names
│   ├── pipeline.py            # orchestrates the full flow
│   ├── validation.py          # image checks (size, format, blur, subject size)
│   ├── segmentation.py        # background removal (swappable backends)
│   ├── species/
│   │   ├── identify.py        # species ID provider interface + implementations
│   │   ├── database.py        # loads and validates species/*.yaml
│   │   └── schema.py          # pydantic models for species files
│   ├── structure.py           # rough branch/foliage estimate (range, not exact)
│   ├── styles.py              # style catalog (ids, names, descriptions), suitability logic
│   └── ui/
│       └── components.py      # Gradio UI pieces, profile card rendering
├── species/                   # one YAML file per species (community-contributed)
│   ├── _template.yaml
│   └── juniperus_procumbens.yaml
├── examples/
│   ├── inputs/                # sample bonsai photos (license-cleared only)
│   └── outputs/
├── docs/
│   ├── architecture.md
│   └── adding-a-species.md
└── tests/
    ├── test_validation.py
    ├── test_species_database.py
    ├── test_styles.py
    └── test_pipeline.py
```

---

## 5. Features to build (v0.1 scope)

### 5.1 Photo input
- Upload JPG/PNG via file picker or drag-and-drop.
- Include 3-5 **built-in sample photos** so visitors can try without uploading.
- Validation: max file size (default 10 MB), allowed formats, minimum resolution, **warn (don't block)** if the image looks blurry or the tree is very small in the frame.

### 5.2 Background removal
- Automatically isolate the tree and pot.
- Show the isolated preview before continuing.
- Implement behind a `Segmenter` interface so backends (rembg, SAM) can be swapped.

### 5.3 Tree Profile card
Displayed right after upload and segmentation, before styling.

- **Predicted species** with a **confidence score**.
- **Common name** and **scientific name**.
- **Species override:** dropdown listing all species in `species/` so the user can correct a wrong prediction. The corrected species drives everything downstream.
- **Quick facts:** origin, difficulty level (beginner / intermediate / advanced).
- **Bonsai practices:** light, watering, pruning season, wiring notes, repotting interval, common problems.
- **Suitable styles** for the species.
- **Rough structure estimate:** approximate number of visible branches or foliage pads as a **range** (e.g., "about 8-12 visible branches"), clearly labeled as an estimate.
- If the species is not in the database or confidence is low, show a clear "Unknown or low confidence, please choose a species" state. Never invent care data.

### 5.4 Styles in the profile
Three styles in v0.1: **Informal upright (Moyogi)**, **Slanting (Shakan)**, **Windswept (Fukinagashi)**.

- The Tree Profile lists all three with a short description. Styles that don't suit the species are labeled **"not recommended"** (shown, not hidden).
- No image generation (dropped; see §1).

### 5.7 Running it
- One-command local setup: `docker compose up` (and a documented non-Docker path using `pip install -e .` then `python app.py`).
- Config through environment variables (`.env.example` provided).
- Deployable as a Hugging Face Space.

### 5.8 Repo essentials
- `README.md`: screenshot at top, demo link, features, quick start, roadmap, how to contribute.
- `LICENSE`: **Apache-2.0** unless the owner says otherwise (confirm with the owner before the first release).
- `MODEL_LICENSES.md`: every model and weight with its license and whether it's bundled or downloaded at runtime.
- `CONTRIBUTING.md` and `docs/adding-a-species.md`.
- Issue and PR templates. Create 5-10 issues labeled `good first issue` / `help wanted` (e.g., "add species X", "add sample photo", "improve blur detection").

---

## 6. Species data format

Each species is one YAML file in `species/`, validated by a pydantic schema in `src/katachi/species/schema.py`.

```yaml
# species/_template.yaml
id: juniperus_procumbens            # lowercase, underscores, unique
common_names: ["Japanese garden juniper", "Dwarf juniper"]
scientific_name: "Juniperus procumbens"
family: "Cupressaceae"
origin: "Japan (Ryukyu Islands)"
difficulty: beginner                # beginner | intermediate | advanced
type: conifer                       # conifer | deciduous | broadleaf_evergreen | tropical
light: "Full sun, at least 6 hours daily."
watering: "Let the topsoil dry slightly between waterings; never let the root ball dry out completely."
pruning:
  season: "Spring to early summer; light pinching year-round."
  notes: "Pinch new growth with fingers; avoid cutting into bare wood without foliage."
wiring:
  season: "Autumn to winter."
  notes: "Branches are flexible; wire carefully to avoid bark damage."
repotting:
  interval: "Every 2-3 years."
  season: "Early spring."
suitable_styles: [informal_upright, slanting, windswept]
not_recommended_styles: []
common_problems:
  - "Spider mites in dry conditions"
  - "Root rot from overwatering"
sources:
  - "Add at least one reliable source (book, nursery, or botanical garden page)."
contributors: ["@github_handle"]
```

Rules:
- **Never fabricate care data.** Every species file must include at least one entry in `sources`.
- Start with **5 species** (e.g., Juniperus procumbens, Ficus microcarpa, Acer palmatum, Pinus thunbergii, Carmona microphylla), then grow to 10-15.
- The schema validator must fail loudly on missing required fields; `test_species_database.py` must validate every file.

---

## 7. Style definitions

Each style in `styles.py` is a small data object (`id`, `display_name`, `description`). Species files reference styles by `id` in `suitable_styles` / `not_recommended_styles`.

---

## 8. Build order (work in these phases)

Complete each phase, run tests, and commit before starting the next.

### Phase 0: Setup
- [ ] Initialize repo structure, `pyproject.toml`, `ruff`, `pytest`, `.gitignore`, `.env.example`.
- [ ] Add placeholder `README.md`, `LICENSE` (Apache-2.0, pending owner confirmation), `MODEL_LICENSES.md`.

### Phase 1: Core pipeline (done)
- [x] `validation.py` with tests.
- [x] `segmentation.py` with `Segmenter` interface and `rembg` backend.
- [x] Simple script (`python -m katachi.pipeline --image x.jpg`) that saves the isolated cutout.
- Restyle was built and then dropped by the owner (see §1).

### Phase 2: Species profile
- [ ] Species schema, loader, and 5 species files.
- [ ] `identify.py` with a provider interface, one working provider, and a "manual only" fallback provider.
- [ ] `structure.py` rough branch/foliage range estimate (heuristic; always output a range with an "estimate" label).
- [ ] Tests for schema validation and database loading.

### Phase 3: Style suitability
- [ ] Suitability logic ("not recommended" labeling) driven by species files.

### Phase 4: UI
- [ ] Gradio app: upload or pick a sample → isolated preview → Tree Profile card (with species override and style suitability).
- [ ] Loading states and clear error messages.

### Phase 5: Packaging and docs
- [ ] `Dockerfile` and `docker-compose.yml`.
- [ ] README with quick start.
- [ ] `CONTRIBUTING.md`, `docs/adding-a-species.md`, `docs/architecture.md`.
- [ ] Hugging Face Space configuration.
- [ ] Issue templates and starter issues list (as a markdown file the owner can post).

---

## 9. Definition of done (v0.1)

- [ ] A stranger can open the demo, pick a sample tree, and see its species profile within a few seconds.
- [ ] Species identification is correct for most common species on the test photos, and the manual override always works.
- [ ] Someone can run it locally by following the README alone.
- [ ] All tests pass; `ruff` is clean.
- [ ] `MODEL_LICENSES.md` is complete and no model weights are committed to the repo.

---

## 10. Out of scope for v0.1 (do NOT build)

- AI restyle / image generation of any kind (dropped by the owner)
- Exact branch counts, health or disease diagnosis, precise measurements
- Mobile app (Flutter / React Native)
- Achievability scoring and pruning/wiring guides
- Manual trunk drawing and cleanup brush
- Growth timeline, reminders, user accounts
- Community gallery and datasets

If something seems necessary that is not in scope, **ask the owner first** instead of adding it.

---

## 11. Rules for Claude Code

1. **Work phase by phase.** Finish and test one phase before starting the next. Summarize what you did at the end of each phase.
2. **Ask before big decisions.** This includes changing the stack, adding a major dependency, or choosing the license. Offer 2-3 options with a recommendation.
3. **Do not commit model weights, API keys, or user photos.** Download weights at runtime or document how to get them. Keep secrets in `.env` (never committed).
4. **Check licenses.** Before adding any model, library, dataset, or sample photo, record its license in `MODEL_LICENSES.md`. Only use sample photos that are public domain or permissively licensed (e.g., CC0, CC BY), with attribution recorded.
5. **Never fabricate horticultural facts.** Care data must come from sourced species files. If unsure, leave a field out and flag it with a TODO instead of guessing.
6. **Be honest in the UI.** Label estimates as estimates and show confidence scores.
7. **Keep components swappable.** Segmentation and species identification sit behind small interfaces so contributors can add alternatives.
8. **Write tests** for validation, species loading, style logic, and the pipeline (using small fixtures and mocked model calls so tests run without downloading models).
9. **Keep code clean and documented.** Type hints, short docstrings, `ruff`-clean, small focused modules.
10. **Commit often** with clear messages (e.g., `feat: add rembg segmentation backend`). One logical change per commit.
11. **Performance:** prefer lazy model loading and caching so the app starts fast and re-runs are quick.
12. **Stop and report** if results look poor (bad cutouts, wrong species). Show the failing examples and propose fixes before moving on.

---

## 12. First message to Claude Code

Paste this into Claude Code to begin:

> Read `CLAUDE.md` fully. Start with **Phase 0: Setup**. Create the repo structure, config files, and placeholders exactly as described. When done, summarize what you created, list any decisions you need from me (especially the license and the species identification provider), and then proceed to Phase 1.

---

## 13. Owner decisions and open questions

Decided: Apache-2.0 license; Pl@ntNet as the default species ID provider; sample photos from Wikimedia Commons (CC0 / public domain / CC BY only); AI restyle dropped.

Open:
- New tagline.
- Hosting for the demo: Hugging Face Space (free CPU should suffice now) or other?
