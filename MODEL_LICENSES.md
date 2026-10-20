# Models, weights, and third-party licenses

Every model, weight, dataset, and sample photo used by Katachi is listed here **before** it is
added to the code. No weights are committed to this repository; all are downloaded at runtime
(Hugging Face models to `~/.cache/huggingface`, rembg models to `~/.u2net`).

## Models and weights

| Component | Model / weights | Source | License | Bundled or runtime download | Notes |
|---|---|---|---|---|---|
| Background removal | U2-Net (`u2net`) via rembg | [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net), served from rembg releases | Apache-2.0 | Runtime download | Default segmenter |
| Restyle base model | Stable Diffusion v1.5 (`stable-diffusion-v1-5/stable-diffusion-v1-5`, fp16 variant on GPU/MPS) | [Hugging Face](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) | [CreativeML OpenRAIL-M](https://huggingface.co/spaces/CompVis/stable-diffusion-license) | Runtime download | OpenRAIL-M use restrictions (Attachment A) pass on to users; must be referenced in README before release. Includes the CompVis safety checker. |
| Restyle ControlNet (edges) | `lllyasviel/control_v11p_sd15_canny` | [Hugging Face](https://huggingface.co/lllyasviel/control_v11p_sd15_canny) | CreativeML OpenRAIL-M | Runtime download | |
| Restyle ControlNet (depth) | `lllyasviel/control_v11f1p_sd15_depth` | [Hugging Face](https://huggingface.co/lllyasviel/control_v11f1p_sd15_depth) | CreativeML OpenRAIL-M | Runtime download | Only loaded for styles using depth conditioning |
| Depth estimator | `Intel/dpt-hybrid-midas` | [Hugging Face](https://huggingface.co/Intel/dpt-hybrid-midas) | Apache-2.0 | Runtime download | Produces depth maps for the depth ControlNet |
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
| torch | BSD-3-Clause | Model inference |
| diffusers | Apache-2.0 | SD + ControlNet pipelines |
| transformers | Apache-2.0 | Text encoder, depth estimation |
| accelerate | Apache-2.0 | Model loading |
| opencv-python-headless | Apache-2.0 (OpenCV), MIT (wrapper) | Canny edge maps |

## Sample photos

Only public domain or permissively licensed photos (CC0, CC BY) with attribution recorded.
CC BY-SA is avoided because share-alike would extend to restyled outputs.

| File | Author | Source | License |
|---|---|---|---|
| _None committed yet; candidates under review for Phase 1 checkpoint._ | | | |
