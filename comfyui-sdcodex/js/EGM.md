# comfyui-sdcodex/js (ComfyUI Web Extensions)

## Overview

The browser-extension layer of the `comfyui-sdcodex` ComfyUI node pack. Each
file registers one ComfyUI extension via `app.registerExtension` and adds a DOM
widget to its matching node type. The four files are:

- `sdcodex_gallery.js` — the legacy `SDCodexGallery` node widget (grid, paging,
  search, selection).
- `sdcodex_gallery_browser.js` — the `SDCodexGalleryBrowser` node widget plus the
  shared selection helpers exported on `window.SDCodexGalleryHelpers`.
- `sdcodex_gallery_loader.js` — a sizing hook for `SDCodexGalleryLoader`.
- `sdcodex_gallery_runner.js` — the `SDCodexGalleryRunner` controls (Start/Stop)
  and the batch loop that queues ComfyUI prompts.

The Python node classes these extend live in the parent directory
([`../EGM.md`](../EGM.md)).

## Interface

- `sdcodex_gallery.js`
  - `app.registerExtension` — extension `SDCodex.GallerySelector` with a
    `nodeCreated(node)` hook that early-returns unless
    `node.comfyClass === "SDCodexGallery"`.
  - `node.addDOMWidget` — registers DOM widget `sdcodex_gallery_widget` of type
    `custom_gallery` on `SDCodexGallery`.
- `sdcodex_gallery_browser.js`
  - `app.registerExtension` — extension `SDCodex.GalleryBrowser` with a
    `nodeCreated(node)` hook that early-returns unless
    `node.comfyClass === "SDCodexGalleryBrowser"`.
  - `window.SDCodexGalleryHelpers` — global object exposing
    `{setWidget, getWidget, syncSelectionNodes, findLoaderNodes}`.
  - `setWidget(node, name, val)` — sets a named widget's `value`, its
    `inputEl.value`, and invokes its `callback(val)`.
  - `getWidget(node, name)` — returns the named widget's value or `""`.
  - `findLoaderNodes(graph)` — returns all graph nodes whose
    `comfyClass === "SDCodexGalleryLoader"`.
  - `syncSelectionNodes(selectedImage, caption, sdPrompt, sdNegative, graph, browserRoot)`
    — broadcasts a selection onto the browser node plus every loader node.
  - `node.addDOMWidget` — registers DOM widget `sdcodex_gallery_widget` of type
    `custom_gallery` on `SDCodexGalleryBrowser`.
- `sdcodex_gallery_loader.js`
  - `app.registerExtension` — extension `SDCodex.GalleryLoader` with a
    `beforeRegisterNodeDef(nodeType, nodeData, app)` hook that early-returns
    unless `nodeData.name === "SDCodexGalleryLoader"`; it wraps
    `nodeType.prototype.onNodeCreated`.
- `sdcodex_gallery_runner.js`
  - `app.registerExtension` — extension `SDCodex.GalleryRunner` with a
    `nodeCreated(node)` hook that early-returns unless
    `node.comfyClass === "SDCodexGalleryRunner"`.
  - `node.addDOMWidget` — registers DOM widget `sdcodex_runner_widget` of type
    `runner_controls` on `SDCodexGalleryRunner`.
  - `startBtn.click` — the Start button invokes the internal `runLoop()`.
  - `stopBtn.click` — the Stop button invokes the internal `stopLoop()`.

## Invariants

- `sdcodex_gallery.js:loadGallery` — reads widgets `mode` (default
  `"Saved Gallery"`), `folder_path` (default `""`) and `sdcodex_root`
  (default `""`), and builds `/sdcodex/images` with `page` and `limit=24`.
- `sdcodex_gallery.js:renderGrid` — `prevBtn.disabled = currentPage <= 1` and
  `nextBtn.disabled = currentPage >= totalPages`.
- `sdcodex_gallery.js:renderGrid` — the search filter matches `img.file_name`
  **or** `img.caption`, case-insensitively; an empty filter passes everything.
- `sdcodex_gallery.js:galleryWidget.serializeValue` — `serializeValue = () => undefined`,
  so the HTML container is never serialized into the workflow.
- `sdcodex_gallery.js:node.min_size` / `node.size` — dimension contract
  `min_size = [350, 720]`, `size = [500, 800]`.
- `sdcodex_gallery.js:node.onResize` — the gallery height is
  `Math.max(320, size[1] / 2)` and the grid height is `galleryHeight - 80`.
- `sdcodex_gallery.js:prevBtn` / `nextBtn` handlers — paging only moves when
  `currentPage > 1` (prev) or `currentPage < totalPages` (next), and
  `currentPage = 1` is restored when the `mode` / `folder_path` / `sdcodex_root`
  widget callbacks fire.
- `sdcodex_gallery_browser.js:loadGallery` — requests
  `/sdcodex/images?folder_path=...&page=...&limit=24`; `totalPages` defaults to
  `1` and `imagesData` to `[]` when absent.
- `sdcodex_gallery_browser.js:renderGrid` — a click sets `selected_image`,
  `caption`, `sd_prompt` and `sd_negative` from `img.*`, each defaulting to `""`.
- `sdcodex_gallery_browser.js:galleryWidget.serializeValue` —
  `serializeValue = () => undefined`.
- `sdcodex_gallery_browser.js:node.min_size` / `node.size` — dimension contract
  `min_size = [350, 400]`, `size = [500, 700]`.
- `sdcodex_gallery_browser.js:node.onResize` — the gallery height is
  `Math.max(200, size[1] - 90)` and the grid element is forced to `height: 100%`.
- `sdcodex_gallery_loader.js:nodeType.prototype.onNodeCreated` — loader node
  sizing contract `min_size = [350, 200]`, `size = [400, 300]`.
- `sdcodex_gallery_runner.js:runLoop` — re-entrancy guard: when `running` is
  true the loop reports `"Already running — press ■ Stop first"` and returns.
- `sdcodex_gallery_runner.js:runLoop` — requires a browser node (the
  `current_image` link source, otherwise the first `SDCodexGalleryBrowser` in the
  graph) and a non-empty `folder_path`, else it aborts with a status message.
- `sdcodex_gallery_runner.js:runLoop` — `max_images` defaults to 0 (run to the
  end of the list via `parseInt(... || "0")`); `executions_per_image` is clamped
  with `Math.max(1, parseInt(... || "1"))`.
- `sdcodex_gallery_runner.js:runLoop` —
  `endIdx = maxImages > 0 ? Math.min(images.length, startIdx + maxImages) : images.length`;
  `startIdx` falls back to 0 when the selected image is not found.
- `sdcodex_gallery_runner.js:waitForPrompt` — one execution is treated as
  finished on `execution_success`, `execution_interrupted`, or `execution_error`
  whose `prompt_id` is absent or equals the queued id; all three listeners are
  removed in `finish()`.
- `sdcodex_gallery_runner.js:queueCurrentGraph` — throws
  `"ComfyUI queue API unavailable"` unless `app.graphToPrompt` is a function and
  `app.api` exists; it queues via `app.api.queuePrompt(0, p)` and returns
  `res.prompt_id`.
- `sdcodex_gallery_runner.js:runLoop` — the inner execution loop breaks on
  `stopRequested`; the done message distinguishes `"max images reached"` from
  `"reached end of list"`.
- `sdcodex_gallery_runner.js:node.min_size` / `node.setSize` — runner node sizing
  contract `min_size = [340, 120]`, `setSize([360, 130])`.

## Side Effects

- `sdcodex_gallery.js:style` / `document.head.appendChild` — injects a `<style>`
  block with `.sdcodex-gallery-*` rules into `document.head` at module load.
- `sdcodex_gallery_browser.js:style` / `document.head.appendChild` — injects its
  own `.sdcodex-gallery-*` `<style>` block into `document.head` at module load.
- `sdcodex_gallery_runner.js:style` / `document.head.appendChild` — injects a
  `.sdcodex-runner-*` `<style>` block into `document.head` at module load.
- `sdcodex_gallery.js:container` / `grid` DOM — builds the gallery DOM
  (`input`, buttons, grid) and mutates `grid.innerHTML` for the Loading / error /
  No-images states and for per-image items.
- `sdcodex_gallery_browser.js:container` / `grid` DOM — builds the gallery DOM
  and rewrites `grid.innerHTML` for the Loading / error / No-images states and
  per-image items.
- `sdcodex_gallery_runner.js:container` DOM — creates the Start / Stop buttons
  and a status `<div>`; `setStatus` writes `statusEl.textContent`.
- `sdcodex_gallery.js:fetch(/sdcodex/images)` — network GET with `mode`,
  `folder_path`, `sdcodex_root`, `page` and `limit=24`.
- `sdcodex_gallery_browser.js:fetch(/sdcodex/images)` — network GET with
  `folder_path`, `page` and `limit=24`.
- `sdcodex_gallery_runner.js:loadFolderImages` fetch — network GET
  `/sdcodex/images?folder_path=...&page=1&limit=100000`.
- `sdcodex_gallery.js:renderGrid` `thumbUrl` — image elements load
  `/sdcodex/image?path=<encodeURIComponent(image_path)>`.
- `sdcodex_gallery_browser.js:renderGrid` `thumbUrl` — image elements load
  `/sdcodex/image?path=<encodeURIComponent(image_path)>`.
- `sdcodex_gallery.js:item` click — mutates the node widget values
  `selected_image` and `caption` (invoking their callbacks) and calls
  `app.graph.setDirtyCanvas(true, true)`.
- `sdcodex_gallery_browser.js:item` click — mutates the widgets
  `selected_image` / `caption` / `sd_prompt` / `sd_negative` on the browser and
  on all `SDCodexGalleryLoader` nodes via `syncSelectionNodes`, then calls
  `app.graph.setDirtyCanvas(true, true)`.
- `sdcodex_gallery.js:setTimeout` widget-callback wrapping — overrides the
  `mode`, `folder_path` and `sdcodex_root` widget `callback` functions,
  chaining the original first.
- `sdcodex_gallery_browser.js:setTimeout` widget-callback wrapping — overrides
  the `folder_path` widget `callback`, chaining the original first.
- `sdcodex_gallery.js:node.onResize` — replaces `node.onResize`, chaining
  `origOnResize`, and writes `gridEl.style.height`, `galleryWidget.height` and
  `container.style.height`.
- `sdcodex_gallery_browser.js:node.onResize` — replaces `node.onResize`, chaining
  `origOnResize`, and sets `galleryWidget.height` / `container.style.height` and
  the grid height.
- `sdcodex_gallery_loader.js:nodeType.prototype.onNodeCreated` — mutates the
  shared node prototype's `onNodeCreated` and assigns `this.min_size` / `this.size`.
- `sdcodex_gallery_runner.js:app.api.queuePrompt` — queues the serialized graph
  (`app.graphToPrompt()` → `app.api.queuePrompt(0, p)`); a ComfyUI prompt-queue
  mutation.
- `sdcodex_gallery_runner.js:app.api.addEventListener` — subscribes and
  unsubscribes `execution_success` / `execution_interrupted` / `execution_error`
  listeners on `app.api`.
- `sdcodex_gallery_runner.js:stopLoop` → `app.api.interrupt()` — interrupts the
  currently executing prompt on the ComfyUI server.
- `sdcodex_gallery_runner.js:helpers.syncSelectionNodes` — mutates widget values
  on the browser and on all loader nodes during the run loop, then calls
  `app.graph.setDirtyCanvas(true, true)`.
- `sdcodex_gallery.js:console.error` — logs load failures to the console.
- `sdcodex_gallery_browser.js:console.error` — logs load failures to the console.
- `sdcodex_gallery_runner.js:console.error` — logs `"Queue error:"`,
  `"Runner error:"` and `"Interrupt error:"`.
- `sdcodex_gallery_runner.js:setStatus` — calls `node.setDirtyCanvas(true, true)`
  when available.

## Verification

- Run: `<test-command>`
