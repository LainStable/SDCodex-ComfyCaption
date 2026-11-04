# comfyui-sdcodex (ComfyUI Node Pack)

## Overview

A vendored ComfyUI custom-node pack that lets a ComfyUI workflow browse a local
image library, load a selected image plus its caption / SD prompts, and replay
the library as a batch. The pack is installed into a ComfyUI `custom_nodes`
directory by the ComfyCaption plugin (see `../betacaption_nodes_backend.py`
and its `install_nodes` route), and it is also usable standalone.

The pack has three surfaces:

- a Python node layer (`__init__.py`, `sdcodex_gallery_browser.py`,
  `sdcodex_gallery_loader.py`, `sdcodex_gallery_runner.py`) that registers the
  node classes and two read-only HTTP routes on ComfyUI's `PromptServer`;
- a browser-extension layer in [`js/`](./js/EGM.md) that renders the gallery
  grid, wires widget values and drives the batch runner;
- an example workflow (`Example Workflow/SDCodex-anima.json`).

## Interface

- `__init__.py`
  - `NODE_CLASS_MAPPINGS` — maps `"SDCodexGalleryBrowser"` →
    `SDCodexGalleryBrowser`, `"SDCodexGalleryLoader"` → `SDCodexGalleryLoader`,
    `"SDCodexGalleryRunner"` → `SDCodexGalleryRunner`.
  - `NODE_DISPLAY_NAME_MAPPINGS` — display names `"SDCodex Gallery Browser"`,
    `"SDCodex Gallery Loader"`, `"SDCodex Gallery Runner"`.
  - `WEB_DIRECTORY` — `"./js"`, the frontend directory ComfyUI serves.
  - `__all__` — `["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]`.
- `sdcodex_gallery_browser.py`
  - `IMAGE_EXTENSIONS` — allow-list `{.jpg, .jpeg, .png, .gif, .webp, .bmp, .avif}`.
  - `get_sdcodex_images` — ComfyUI route `GET /sdcodex/images`
    (query `folder_path`, `page` default 1, `limit` default 24) → `{images:[{file_name, image_path, caption, sd_prompt, sd_negative}], total, page, totalPages, limit}`.
  - `get_sdcodex_image_content` — ComfyUI route `GET /sdcodex/image` (query `path`)
    → raw image bytes with a guessed MIME type.
  - `SDCodexGalleryBrowser` — node class; `RETURN_TYPES = ("STRING","STRING","STRING","STRING","IMAGE")`,
    `RETURN_NAMES = ("selected_image","caption","sd_prompt","sd_negative","image")`,
    `OUTPUT_NODE = True`, `FUNCTION = "execute"`, `CATEGORY = "SDCodex"`.
  - `SDCodexGalleryBrowser.INPUT_TYPES` — required STRING inputs `folder_path`,
    `selected_image`, `caption`, `sd_prompt`, `sd_negative`.
  - `SDCodexGalleryBrowser.execute` — returns the 5-tuple matching `RETURN_NAMES`.
  - `_list_images`, `_resolve_folder`, `_read_sidecar_caption`, `_read_sd_prompt` — helpers.
- `sdcodex_gallery_loader.py`
  - `SDCodexGalleryLoader` — node class; `RETURN_TYPES = ("STRING","IMAGE","STRING","STRING")`,
    `RETURN_NAMES = ("caption","image","sd_prompt","sd_negative")`,
    `FUNCTION = "execute"`, `CATEGORY = "SDCodex"`.
  - `SDCodexGalleryLoader.INPUT_TYPES` — required STRING inputs `selected_image`,
    `caption`, `sd_prompt`, `sd_negative`, `prefix`, `suffix`.
  - `SDCodexGalleryLoader.execute` — returns `(caption, image, sd_prompt, sd_negative)`.
  - `default_sdcodex_root` — module constant: the parent directory when it holds
    `run.py`, else `"/home/naked/dev/SDCodex"`.
- `sdcodex_gallery_runner.py`
  - `SDCodexGalleryRunner` — node class; `RETURN_TYPES = ("STRING",)`,
    `RETURN_NAMES = ("current_image",)`, `OUTPUT_NODE = True`,
    `FUNCTION = "execute"`, `CATEGORY = "SDCodex"`.
  - `SDCodexGalleryRunner.INPUT_TYPES` — required INT `executions_per_image`
    (default 1, 1..999) and INT `max_images` (default 0, 0..100000); optional
    STRING `current_image` with `forceInput = True`.
  - `SDCodexGalleryRunner.execute` — pass-through returning `(current_image or "",)`.
- Subdirectories:
  - [`js/`](./js/EGM.md) — ComfyUI web-extension scripts for the three nodes.

## Invariants

- `sdcodex_gallery_browser.py:_list_images` — a filename is included only when its
  lower-cased extension is in `IMAGE_EXTENSIONS`; results are sorted and list
  errors return `[]`.
- `sdcodex_gallery_browser.py:_resolve_folder` — `folder_path` is stripped and
  must be non-empty and `os.path.isdir`, otherwise `None`.
- `sdcodex_gallery_browser.py:get_sdcodex_images` — an invalid folder returns HTTP
  400 `{"error": "folder_path must be a real directory"}`; `page` is clamped to
  `max(1, page)` and `limit` to `max(1, limit)` before slicing; `totalPages` is
  `ceil(total/limit)` and at least 1.
- `sdcodex_gallery_browser.py:get_sdcodex_image_content` — an empty `path` returns
  400, a missing file 404, and an extension outside `IMAGE_EXTENSIONS` returns 400
  `"File requested is not a valid image format"`.
- `sdcodex_gallery_browser.py:_read_sd_prompt` — embedded metadata is used only
  when it is a non-empty string that does not contain `"workflow"` (ComfyUI
  workflow JSON is rejected); the positive prompt is the first non-empty line and
  the negative prompt is the remainder of the line starting with
  `"negative prompt:"` (case-insensitive), otherwise `("", "")`.
- `sdcodex_gallery_browser.py:_read_sidecar_caption` — the caption is read only
  from a `<base>.txt` sidecar beside the image and only when `os.path.isfile`;
  any failure yields `""`.
- `sdcodex_gallery_browser.py:SDCodexGalleryBrowser.execute` — `selected_image`
  is resolved only when it is absolute and an existing file, otherwise as
  `os.path.join(folder_path, selected_image)` where `folder_path` is an existing
  directory and the joined path is a file; otherwise no image is loaded.
- `sdcodex_gallery_browser.py:SDCodexGalleryBrowser.execute` — supplied
  `caption` / `sd_prompt` / `sd_negative` are backfilled from disk only when
  empty (each field independently); caller values win.
- `sdcodex_gallery_browser.py:SDCodexGalleryBrowser.execute` — the output image
  defaults to `torch.zeros((1,512,512,3), float32)` and is replaced only on a
  successful decode.
- `sdcodex_gallery_loader.py:SDCodexGalleryLoader.execute` — `selected_image` is
  resolved only when absolute and existing, otherwise
  `<default_sdcodex_root>/downloads/<selected_image>` must be a file; something
  must satisfy `os.path.isfile` before loading.
- `sdcodex_gallery_loader.py:SDCodexGalleryLoader.execute` — caption/prompt
  backfill occurs only when the corresponding input is empty.
- `sdcodex_gallery_loader.py:SDCodexGalleryLoader.execute` — `prefix` is
  prepended to `caption` and `sd_prompt` (never to `sd_negative`) with a space
  separator unless the prefix already ends in `,` or ` `; `suffix` is appended
  symmetrically unless it starts with `,` or ` `.
- `sdcodex_gallery_loader.py:SDCodexGalleryLoader.execute` — the output image
  defaults to `torch.zeros((1,512,512,3), float32)` when nothing loads.
- `sdcodex_gallery_runner.py:SDCodexGalleryRunner.INPUT_TYPES` —
  `executions_per_image` is constrained to 1..999 and `max_images` to 0..100000
  (0 means cycle to the end of the image list); `current_image` is `forceInput`
  and therefore cannot be a widget.
- `sdcodex_gallery_runner.py:SDCodexGalleryRunner.execute` — always returns a
  tuple of exactly one string, never `None`.

## Side Effects

- `sdcodex_gallery_browser.py:get_sdcodex_images` — registers a route on
  `PromptServer.instance` at import time via the
  `@PromptServer.instance.routes.get` decorator.
- `sdcodex_gallery_browser.py:get_sdcodex_image_content` — registers a route on
  `PromptServer.instance` at import time and reads the whole file into memory via
  `open(path, "rb").read()`.
- `sdcodex_gallery_browser.py:_list_images` — filesystem read via
  `os.listdir(folder_path)`.
- `sdcodex_gallery_browser.py:_read_sidecar_caption` — filesystem read of
  `<image base>.txt` (utf-8, errors ignored).
- `sdcodex_gallery_browser.py:_read_sd_prompt` — opens the image with PIL to read
  embedded `prompt` / `parameters` PNG metadata.
- `sdcodex_gallery_browser.py:get_sdcodex_image_content` — `mimetypes.guess_type`
  on the served path.
- `sdcodex_gallery_browser.py:SDCodexGalleryBrowser.execute` — filesystem
  existence checks (`os.path.isabs` / `isfile` / `isdir`), a PIL `Image.open` of
  the selected file, and a `print` of the load failure.
- `sdcodex_gallery_browser.py:SDCodexGalleryBrowser.execute` — allocates torch
  tensors (a new float32 tensor of shape `(1,512,512,3)` or the decoded image);
  input nodes are not mutated.
- `sdcodex_gallery_loader.py:_read_sidecar_caption` — filesystem read of
  `<image base>.txt`.
- `sdcodex_gallery_loader.py:_read_sd_prompt` — PIL open of the image to read
  embedded prompt/parameters metadata.
- `sdcodex_gallery_loader.py:SDCodexGalleryLoader.execute` — `os.path.exists` /
  `os.path.isfile` stats, a PIL `Image.open` of the resolved path, a `print` of
  the load failure, and torch tensor allocation.
- `sdcodex_gallery_loader.py:default_sdcodex_root` — import-time
  `os.path.exists` check for `<parent>/run.py`.
- `sdcodex_gallery_runner.py:SDCodexGalleryRunner.execute` — no filesystem,
  network, logging, or tensor effects; a pure string pass-through.

## Verification

- Run: `<test-command>`
