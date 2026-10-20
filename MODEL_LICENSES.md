# Models, weights, and third-party licenses

Every model, weight, dataset, and sample photo used by Katachi is listed here **before** it is
added to the code. No weights are committed to this repository; all are downloaded at runtime
(rembg models to `~/.u2net`).

## Models and weights

| Component | Model / weights | Source | License | Bundled or runtime download | Notes |
|---|---|---|---|---|---|
| Background removal | U2-Net (`u2net`) via rembg | [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net), served from rembg releases | Apache-2.0 | Runtime download | Default segmenter |
| Species identification | Pl@ntNet API | [my.plantnet.org](https://my.plantnet.org/) | Pl@ntNet API terms of service | Hosted API | Phase 2; terms to be reviewed when integrated |

## Key libraries

| Library | License | Used for |
|---|---|---|
| numpy | BSD-3-Clause | Image math |
| Pillow | MIT-CMU (HPND) | Image I/O |
| pydantic | MIT | Species schema |
| PyYAML | MIT | Species files |
| python-dotenv | BSD-3-Clause | `.env` loading |
| rembg | MIT | Background removal |
| onnxruntime | MIT | rembg inference |

## Sample photos

Only public domain or permissively licensed photos (CC0, CC BY) with attribution recorded.
CC BY-SA is avoided to keep sample reuse simple.

| File | Author | Source | License |
|---|---|---|---|
| _None committed yet; candidates under review._ | | | |
