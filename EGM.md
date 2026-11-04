# ComfyCaption Plugin

## Overview

The **ComfyCaption** plugin captions images with a local or remote
OpenAI-compatible vision model (LM Studio, Ollama, an OpenAI-compatible
endpoint) and exposes the result as a `<stem>.txt` sidecar next to the image.
It also ships a vendored FolderFrame browser so the captioning studio can
browse a media library without the Gallery plugin installed, and a ComfyUI node
pack that lets a ComfyUI workflow pick images from the same library.

The plugin is split across several Python modules:

- `plugin.py` — the plugin entry point; registers the blueprints.
- `betacaption_backend.py` — the captioning core (single caption, batch,
  status, folder browsing).
- `betacaption_models_backend.py` — the local GGUF vision-model manager
  (HuggingFace download, token storage).
- `betacaption_nodes_backend.py` — installs the bundled ComfyUI node pack.
- `betacaption_gallery_browser.py` — the vendored Gallery browser backend.
- `comfyui-sdcodex/` — the ComfyUI node pack itself.

## Interface

### `plugin.py`

- `init_plugin(app, db, plugin_info=None)` — registers the `beta_caption_bp`,
  `beta_caption_models_bp` and `beta_comfyui_nodes_bp` blueprints plus the
  optional vendored `betacaption_gallery` blueprint, and returns `True`.

### `betacaption_backend.py` — blueprint `caption_bp` (url_prefix `/betacaption/api`)

- `check_connection` — `POST /check-connection`.
- `get_file` — `GET /file`.
- `get_images` — `GET /images`.
- `save_caption` — `POST /save-caption`.
- `caption_single` — `POST /caption-single`.
- `start_caption_batch` — `POST /batch/start`.
- `caption_batch` — `POST /caption` (a `text/event-stream` of the batch events).
- `caption_batch_status` — `GET /batch/status`.
- `caption_task` — `GET /task`.
- `stop_caption_batch` — `POST /batch/stop`.
- `download_workflow` — `GET /workflow`.
- `browse_folders` — `GET /browse-folders`.
- `browse_roots` — `GET /browse-roots`.
- `list_folders` — `GET /folders`.
- `status` — `GET /status`.
- Constant — `IMAGE_EXTENSIONS` (`.jpg .jpeg .png .webp .gif .bmp`).

### `betacaption_models_backend.py` — blueprint `models_bp` (url_prefix `/betacaption/models`)

- `status_route` — `GET /status`.
- `list_models` — `GET /list`.
- `token_status` — `GET /token-status`.
- `save_token` — `POST /token`.
- `save` — `POST /save`.
- `download` — `POST /download`.
- `stop` — `POST /stop`.
- Public helpers — `load_settings`, `save_settings`, `start_download`, `stop_download`.
- Constants — `DEFAULT_REPO` (`nakedlittlezombie/Qwen3-VL-8B-Thinking-heretic`),
  `MODEL_OPTIONS`, `HF_ENDPOINT`, `CHUNK`.

### `betacaption_nodes_backend.py` — blueprint `nodes_bp` (url_prefix `/betacaption/models/nodes`)

- `get_config` — `GET ""`.
- `set_directory` — `PUT /directory`.
- `install_nodes` — `POST /install`.
- Constants — `PLUGIN_DIR`, `NODE_PACK`, `NODE_PACK_NAME` (`comfyui-sdcodex`).

### `betacaption_gallery_browser.py` — blueprint `gallery_bp` (url_prefix `/betacaption/gallery/api`)

- `legacy_ui_asset` — `GET /legacy-ui/<path:filename>`.
- `folderframe_config` — `GET /folderframe.config.json`.
- `optimize_status_compat` — `GET /optimize-status`.
- `folderframe_browse` — `GET /browse/` and `GET /browse/<path:relpath>`.
- `picker_list` — `GET /picker/list`.
- `picker_file` — `GET /picker/file`.
- `gallery_status` — `GET /status` (optional `?counts=1`).
- `list_folders` — `GET /folders`.
- `list_media` — `GET /media`.
- `get_media_file` — `GET /file/<path:relpath>`.
- `get_media_meta` — `GET /meta`.
- `save_caption` — `POST /caption`.
- `download_workflow` — `GET /workflow`.
- `rescan_cache` — `POST /rescan`.
- `caption_target` — `GET /caption-target`.
- `get_prompt` — `GET /prompt`.
- `browse_folders` — `GET /browse-folders`.
- `browse_roots` — `GET /browse-roots`.
- `export_workflows` — `GET /export-workflows`.
- `optimize_media` — `POST /optimize`.
- `convert_media` — `POST /convert`.
- Public helpers — `require_login`, `resolve_browse_root`, `is_safe_path`,
  `resolve_file`, `extract_comfy_workflow`, `read_sidecar_caption`,
  `read_embedded_caption`, `read_prompts_and_settings`, `guess_model_badge`,
  `format_bytes`.
- Constants — `IMAGE_EXTENSIONS`, `VIDEO_EXTENSIONS`, `MEDIA_EXTENSIONS`,
  `PICKER_IMAGE_EXTENSIONS`, `_PICKER_WALK_LIMIT`, `EXIF_FIELDS`.

### Subdirectories

- [`comfyui-sdcodex/`](./comfyui-sdcodex/EGM.md) — the bundled ComfyUI node pack
  (Python nodes plus the [`js/`](./comfyui-sdcodex/js/EGM.md) web extensions).
- [`legacy-ui/`](./legacy-ui/EGM.md) — the vendored FolderFrame browser front end,
  forked to the `/betacaption` prefix.

## Invariants

- `betacaption_backend.py:_caption_auth_guard` — the `before_request` hook on
  `caption_bp` returns 401 `{"error":"unauthorized"}` whenever
  `_core_session_missing()` is `True`.
- `betacaption_backend.py:_caption_auth_guard` — any request path ending in
  `"/status"` is exempt from the auth guard.
- `betacaption_backend.py:_core_session_missing` — returns `False` when the
  `sdcodex` core package is not importable (a standalone deployment) and `True`
  when `current_user()` raises.
- `betacaption_backend.py:IMAGE_EXTENSIONS` — every image considered by
  `get_file`, `get_images`, `save_caption`, `_start_caption_batch` and
  `list_folders` must have an extension in the lower-cased allow-list.
- `betacaption_backend.py:get_file` — the file name is reduced via `os.path.basename`
  and must pass `_is_safe_path(folder_path, image_path)` plus `os.path.isfile`.
- `betacaption_backend.py:save_caption` — the file name is `os.path.basename`d,
  must pass `_is_safe_path`, and the caption must be a `str` (400 "Caption must be text").
- `betacaption_backend.py:caption_single` — rejects with 400 "Invalid fileName"
  when `_is_safe_path(folder_path, image_path)` fails; 404 if the image is
  missing; 500 if `openai` is unavailable.
- `betacaption_backend.py:_is_safe_path` — containment is decided by
  `os.path.commonpath` over `os.path.realpath(base/target)`, returning `False`
  on a `ValueError`.
- `betacaption_backend.py:download_workflow` — requires `_is_safe_path(folder_path,
  image_path)` and an existing file before extracting the metadata.
- `betacaption_backend.py:_start_caption_batch` — returns 409
  `{"error":"A caption batch is already running", jobId}` while `_batch["state"]`
  is `"running"` or `"cancelling"` (a single concurrent batch).
- `betacaption_backend.py:_start_caption_batch` — validates in order: the
  folderPath exists (400), `openai` is installed (500), the LLM is reachable via
  `models.list(timeout=5.0)` (500), and the image list is non-empty (400).
- `betacaption_backend.py:_start_caption_batch` — the `job_id` is monotonic
  (`_batch["job_id"] + 1`) and the state is set to `"running"` with fresh
  events / cancel / last_error / started_at before the thread starts.
- `betacaption_backend.py:_batch_emit` — events from a stale `job_id` are
  dropped (`job_id != _batch["job_id"]` returns early).
- `betacaption_backend.py:_batch_emit` — the `eventId` is monotonic, the event
  list is truncated to the last 300 entries, and a status of `"complete"` /
  `"cancelled"` sets the state while `"error"` only stores `last_error`.
- `betacaption_backend.py:_run_caption_batch` — the worker stops iterating when
  the `job_id` no longer matches or `_batch["cancel"]` is set, then emits
  `"cancelled"` versus `"complete"` based on the final state.
- `betacaption_backend.py:_run_caption_batch` — `mode == "missing"` skips any
  file whose sibling `.txt` already exists (emitting a success status with `skipped:true`).
- `betacaption_backend.py:caption_batch` — the SSE generator terminates when the
  `job_id` changes or the state is `"complete"` / `"cancelled"`, and the
  last-event-id tracking prevents replaying events.
- `betacaption_backend.py:caption_batch_status` — the events are filtered to
  `eventId > since`, with `since` clamped to ≥ 0.
- `betacaption_backend.py:caption_task` — reports `active:true` only while the
  state is `"running"` or `"cancelling"`.
- `betacaption_backend.py:stop_caption_batch` — only transitions
  `running → cancelling`; other states are returned unchanged with `ok:true`.
- `betacaption_backend.py:_reachable_url` — `localhost` / `127.0.0.1` is
  rewritten to the Docker gateway only when `_in_docker()` is true; it falls
  back to `http://localhost:1234/v1` on an empty input.
- `betacaption_backend.py:browse_folders` — entries starting with `"."` are
  skipped and the directory list is capped at 500.
- `betacaption_backend.py:list_folders` — dot entries, `__pycache__` and
  `node_modules` are skipped, and the counting stops at 9999 images per folder.
- `plugin.py:init_plugin` — the blueprint registration is idempotent, guarded by
  the `app.blueprints` name checks (`"beta_caption_bp"`, `"beta_caption_models_bp"`,
  `"beta_comfyui_nodes_bp"`, `"betacaption_gallery"`).
- `plugin.py:init_plugin` — the vendored gallery browser is optional: an
  `ImportError` or exception only logs a warning and returns `True` regardless.
- `betacaption_models_backend.py:_models_auth_guard` — every `models_bp` request
  returns 401 `{"error":"unauthorized"}` when the core auth module is importable
  and `current_user()` is `None`.
- `betacaption_models_backend.py:_core_session_missing` — standalone deployments
  without `sdcodex.auth` are treated as authenticated; any exception in
  `current_user()` is treated as unauthenticated.
- `betacaption_models_backend.py:save_token` — the stored token is stripped of
  its surrounding whitespace before persistence.
- `betacaption_models_backend.py:save` — an empty / blank `repo` is coerced back
  to `DEFAULT_REPO`.
- `betacaption_models_backend.py:list_models` — `token_status` / `list_models`
  expose only a configured boolean and the repo; the raw `hf_token` is never
  serialized there.
- `betacaption_models_backend.py:save` — however `save` echoes the full merged
  settings dict, which includes `hf_token`.
- `betacaption_models_backend.py:start_download` — unknown `option_key` values
  are rejected without starting a thread (the `MODEL_OPTIONS` allow-list).
- `betacaption_models_backend.py:start_download` — before spawning a new thread
  the job is cancelled and `generation` is incremented, so stale workers detach
  from the current job.
- `betacaption_models_backend.py:_download_one` — the worker aborts if
  `_job.cancel` is set or `_job.generation != gen`, setting the state `"cancelled"`.
- `betacaption_models_backend.py:_run_download` — the final state is written only
  when `_job.generation == gen`; the terminal states are `"cancelled"`, `"done"`
  (all files ok) or `"error"`.
- `betacaption_models_backend.py:_download_one` — resume semantics: the partial
  file is `<dest>.incomplete`; an HTTP 200 on a ranged request resets the progress
  to 0 and deletes the partial.
- `betacaption_models_backend.py:_run_download` — files already present with a
  size > 0 and no `.incomplete` are skipped.
- `betacaption_models_backend.py:_list_models` — files ending in `.incomplete`,
  `.json` or `.partial` are excluded from the present-models listing.
- `betacaption_models_backend.py:_job` — there is exactly one process-wide job
  (`_job`) and one thread handle (`_job_thread`); all state fields are mutated
  under `_job.lock`.
- `betacaption_nodes_backend.py:_admin_required` — all `nodes_bp` routes require
  a signed-in user (401) that is an admin (403).
- `betacaption_nodes_backend.py:_validate_install_dir` — the install directory
  must be non-empty, an existing directory and contain `main.py`, else a `ValueError`.
- `betacaption_nodes_backend.py:_node_destination` — `custom_nodes` must not be
  a symlink or a non-directory, and its realpath must remain inside the realpath
  of the install root.
- `betacaption_nodes_backend.py:_node_destination` — an existing SDCodex node-pack
  destination must not be a symlink and must be a directory.
- `betacaption_nodes_backend.py:install_nodes` — it requires a configured
  `comfyui_dir` (409 otherwise); the bundled `NODE_PACK` must exist, be a
  directory, contain `__init__.py` and contain no symlinks.
- `betacaption_nodes_backend.py:install_nodes` — an existing destination that
  contains symlinks is rejected before the copy.
- `betacaption_nodes_backend.py:install_nodes` — `get_config` / `set_directory`
  treat any `OSError` / `ValueError` in the validation as `valid: false` rather
  than raising.
- `betacaption_gallery_browser.py:_gallery_auth_guard` — every `gallery_bp`
  request passes through `require_login()`, returning a 401 JSON when a core
  session is missing.
- `betacaption_gallery_browser.py:is_safe_path` — the path containment is
  decided with `realpath` + `commonpath`, so symlink escapes are rejected; a
  `ValueError` counts as unsafe.
- `betacaption_gallery_browser.py:folderframe_browse` — non-contained browse
  paths return `"Forbidden", 403`.
- `betacaption_gallery_browser.py:_picker_join` — the picker joins resolve
  absolute paths and return `(None, rel)` when `is_safe_path` fails.
- `betacaption_gallery_browser.py:picker_list` — only `PICKER_IMAGE_EXTENSIONS`
  files are listed; dotfiles and `__pycache__` / `node_modules` are skipped; the
  folders are capped at 400 and the images at 600.
- `betacaption_gallery_browser.py:_picker_count` — the recursive count stops at
  `_PICKER_WALK_LIMIT` (4000) and only counts allow-listed image extensions.
- `betacaption_gallery_browser.py:resolve_browse_root` — an explicit
  `GALLERY_ROOT` / `GALLERY` is honored even when the mount is absent (to report
  the real problem) instead of falling back.
- `betacaption_gallery_browser.py:gallery_status` — the recursive library walk
  runs only when `counts` is `1` / `true` / `yes`, keeping plain status calls cheap.
- `betacaption_gallery_browser.py:folderframe_config` — the source switcher is
  local-disk only (`_folderframe_sources` returns a single `media` source).
- `betacaption_gallery_browser.py:read_prompts_and_settings` — JSON-looking
  embedded values are not treated as captions; `read_embedded_caption` skips
  strings starting with `{` or `[`.
- `betacaption_gallery_browser.py:guess_model_badge` — the checks run in a fixed
  order over the lowercased filename and prompt: `flux` wins first, then
  `sdxl` **or** a max dimension ≥ 1024, then `sd3`, `lora`, and
  `illustrious`/`pony`. A ≥ 1024 image is therefore only classified as SDXL
  when no earlier token matched — the dimension rule is not independent of the
  filename and prompt tokens.

## Side Effects

- `betacaption_backend.py:caption_single` — writes the caption sidecar
  `<stem>.txt` beside the image (utf-8) after the LLM reply.
- `betacaption_backend.py:_run_caption_batch` — writes a `<stem>.txt` sidecar per
  captioned image.
- `betacaption_backend.py:save_caption` — writes / overwrites the `<stem>.txt`
  sidecar with `caption.strip()`.
- `betacaption_backend.py:get_images` — reads the `.txt` sidecars, opens each
  image with PIL for the dimensions and calls `os.path.getsize`.
- `betacaption_backend.py:get_file` — reads the image from disk and streams it
  via `send_file` with `Content-Disposition` / `Cache-Control` headers.
- `betacaption_backend.py:check_connection` — a network call to
  `client.models.list()` against the LM Studio base URL, with a `requests.get`
  fallback probe.
- `betacaption_backend.py:caption_single` — a network call to
  `client.chat.completions.create()` with the data-URI image, plus a
  full-resolution base64 read of the file for the display.
- `betacaption_backend.py:_run_caption_batch` — a network call to
  `client.chat.completions.create()` per image and opens an `openai` client bound
  to the target URL.
- `betacaption_backend.py:_start_caption_batch` — a network call to
  `client.models.list(timeout=5.0)` as a reachability probe.
- `betacaption_backend.py:_start_caption_batch` — spawns a daemon
  `threading.Thread` running `_run_caption_batch`.
- `betacaption_backend.py:_batch_emit` — mutates the in-memory `_batch` dict
  (event_id, events, current / total / file, state, last_error) under `_batch_lock`.
- `betacaption_backend.py:stop_caption_batch` — mutates `_batch["cancel"] = True`
  and `_batch["state"] = "cancelling"`.
- `betacaption_backend.py:get_images` — an `os.listdir` of the requested folder
  and an `_extract_comfy_workflow` metadata parse per file.
- `betacaption_backend.py:list_folders` — a recursive `os.walk` of each child
  folder to count the images.
- `betacaption_backend.py:browse_folders` — an `os.listdir` of the requested
  directory and `os.path.exists` / `isdir` stat calls.
- `betacaption_backend.py:_in_docker` — a filesystem check for `/.dockerenv` and
  a read of the `REMBG_OUTPUT` env var.
- `betacaption_backend.py:_docker_default_gateway` — reads `/proc/net/route` to
  derive the gateway IP.
- `betacaption_backend.py:_extract_comfy_workflow` — reads the image metadata via
  PIL / piexif (workflow / prompt keys, EXIF `UserComment`).
- `betacaption_backend.py:_read_sd_info` — instantiates an
  `sd_prompt_reader.ImageDataReader` against the image file.
- `plugin.py:init_plugin` — mutates the process `sys.path` (the plugin directory
  is inserted at index 0 at import time) and imports the
  `betacaption_backend` / models / nodes / gallery_browser modules into the
  shared `sys.modules`.
- `plugin.py:init_plugin` — logs via `app.logger.info` / `app.logger.warning` on
  the blueprint mount and on a gallery-browser failure.
- `betacaption_models_backend.py:_models_dir` — creates the `CAPTION_MODELS` /
  `LMSTUDIO_MODELS` / `<DATA_DIR>/caption_models` / plugin-local
  `caption_models` directory (mkdir); the first writable candidate wins.
- `betacaption_models_backend.py:load_settings` — reads `models_settings.json`
  from the models directory; a missing / corrupt file silently yields `{}`.
- `betacaption_models_backend.py:save_settings` — writes `models_settings.json`
  (mkdir parent, JSON indent=2).
- `betacaption_models_backend.py:_run_download` — a network GET of
  `{HF_ENDPOINT}/api/models/{repo}?blobs=true` (Bearer token when set) to read
  the exact sibling sizes; failures are ignored.
- `betacaption_models_backend.py:_download_one` — a network GET of
  `{HF_ENDPOINT}/{repo}/resolve/main/<file>` with `Range: bytes=<start>-`; it
  streams 1 MiB chunks to `<dest>.incomplete`.
- `betacaption_models_backend.py:_download_one` — on success it atomically
  `os.replace`s the partial onto the destination; on an HTTP 200 with a resume
  offset it removes the stale partial; on auth / 404 / other errors it records
  the `error` state.
- `betacaption_models_backend.py:start_download` — spawns a daemon
  `threading.Thread` running `_run_download`.
- `betacaption_models_backend.py:_download_one` — mutates the in-memory `_job`
  fields (file, state, bytes, speed, message) under `_job.lock`.
- `betacaption_models_backend.py:stop_download` — sets the in-memory
  `_job.cancel = True` and `state = "cancelling"`.
- `betacaption_nodes_backend.py:install_nodes` — copies the bundled node pack
  with `shutil.copytree(..., dirs_exist_ok=True)` into the ComfyUI
  `custom_nodes` directory, ignoring `.git`, `__pycache__` and `*.pyc`.
- `betacaption_nodes_backend.py:install_nodes` — logs `logger.info` on success
  and `logger.exception` on an `OSError` / `shutil.Error`.
- `betacaption_nodes_backend.py:set_directory` — persists `comfyui_dir` into the
  shared settings JSON via `save_settings`.
- `betacaption_gallery_browser.py:legacy_ui_asset` — reads / serves the files
  from `<plugin_dir>/legacy-ui` via `send_from_directory`.
- `betacaption_gallery_browser.py:folderframe_browse` — reads the target
  directory with `os.scandir` for the HTML listing or streams a file with
  `send_file` (inline disposition).
- `betacaption_gallery_browser.py:picker_file` — opens the image with PIL and
  regenerates an in-memory WEBP thumbnail (`quality=82`) when `w>0`, falling
  through to the raw bytes on failure.
- `betacaption_gallery_browser.py:extract_comfy_workflow` — reads the image
  metadata via PIL and an optional piexif EXIF parse (no writes).
- `betacaption_gallery_browser.py:read_sidecar_caption` — reads the
  `<image_basename>.txt` from disk.
- `betacaption_gallery_browser.py:read_embedded_caption` — reads the PIL
  `img.info` and the EXIF `ImageDescription`.
- `betacaption_gallery_browser.py:read_prompts_and_settings` — optionally
  instantiates an `sd_prompt_reader.ImageDataReader` and reads the PIL info /
  Comfy prompt JSON.
- `betacaption_gallery_browser.py:gallery_status` — with `counts=1` it
  recursively walks the library (`os.walk`) counting the media files and directories.
- `betacaption_gallery_browser.py:resolve_browse_root` — creates
  `<workspace>/downloads` when no candidate exists and returns it.
- `betacaption_gallery_browser.py:_picker_count` — recursively walks the target
  folder to count the images (bounded by `_PICKER_WALK_LIMIT`).

## Verification

- Run: `<test-command>`
