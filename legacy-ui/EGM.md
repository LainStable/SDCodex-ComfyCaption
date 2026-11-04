# legacy-ui (FolderFrame Gallery Browser — ComfyCaption vendored copy)

## Overview

The vendored FolderFrame media-browser front end shipped with the **ComfyCaption**
plugin. It is plain ES2020 JavaScript (no build step, no framework) served by
`betacaption_gallery_browser.py` from `<plugin_dir>/legacy-ui`.

**Vendoring status** — this directory is *not* a byte-identical copy of the
canonical browser in [`../../Gallery/legacy-ui/`](../../Gallery/legacy-ui/EGM.md):

- `settings.js` (244 lines), `resilience.js` (258 lines) and
  `folderframe.config.json` (36 lines) are line-for-line identical to the
  canonical equivalents.
- `app.js` is 3990 lines here versus 3987 in the canonical copy. The only
  content differences are 14 endpoint / plugin-id literals (11 `/gallery/api/…`
  endpoints rewritten to the `/betacaption/gallery/api/…` prefix, 3
  `/comfy-caption/api/…` endpoints rewritten to `/betacaption/api/…`, and the
  `comfy-caption` plugin id replaced by `betacaption`) plus 3 extra comment
  lines. All other top-level symbols exist unchanged.

The practical consequence is that **this copy never addresses the stable
`/comfy-caption` prefix**; every server call in it is rooted at `/betacaption`.

Files:

- `app.js` — the browser: source rail, folder grid, virtualized tile window,
  full-screen viewer, slideshow, zoom/pan/rotate gestures, details panel,
  optimize/convert actions and the star store.
- `settings.js` — configuration and URL handling. Global
  `window.FolderFrameSettings` (also `module.exports` under Node).
- `resilience.js` — shared bounded asynchronous work. Global
  `window.FolderFrameResilience` (also `module.exports` under Node).
- `folderframe.config.json` — the shipped configuration (identical to the canonical file).
- `styles.css` — the stylesheet. `heic2any.min.js` — the vendored HEIC decoder.

## Interface

### `app.js`

- Module collaborators
  - `settingsApi` — the `window.FolderFrameSettings` contract consumed by
    `app.js`: `normalizeConfig`, `resolveSettings`, `thumbnailUrl`,
    `relativeMediaPath`, `directoryUrl`, `mediaUrl`.
  - `resilience` — the `window.FolderFrameResilience` contract consumed by
    `app.js`: `createTaskQueue`, `request`, `abortError`.
- Load-order contract — `app.js` is a classic browser-global script with no
  exports; `window.FolderFrameSettings` and `window.FolderFrameResilience` must
  exist before it runs, and every function is a global declaration.
- DOM id contract — the `$ = document.getElementById` binding block resolves
  ~90 ids (`media-viewport`, `media-container`, `gallery-image`, `gallery-video`,
  `thumbnail-grid`, `grid-view-container`, `breadcrumb`, `source-rail-list`,
  `info-*`, `scan-loading`, `scan-progress-track` / `scan-progress-fill`,
  `btn-caption-this`, `caption-this-section`, `convert-overlay`, …). A missing
  element throws during load, not at call time.
- Constants — `DIRECTORY_TIMEOUT` (15000), `MEDIA_TIMEOUT` (30000),
  `GRID_BATCH_SIZE` (100), `GRID_WINDOW_SIZE` (300),
  `SCAN_SIBLING_CONCURRENCY` (5), `IGNORE_SENTINELS`
  (`folderframe.ignore`, `.frameignore`), `IGNORED_DIRECTORY_NAMES`.
- Window message contract — `applyAppTheme` plus the inbound message handler
  accept same-origin `postMessage` of type `sdcodex:theme`
  (`{vars:{bg,card,ink,inkMuted,inkFaint,primary,secondary},mode}`) and
  `sdcodex:set-source` (`{sourceId}`), and re-declare the CSS custom properties
  `--bg/--card-bg/--text/--text-secondary/--border/--primary/--info/--ff-glow/--ff-glow-hover`
  on `documentElement`.
- `renderSourceRail` posts the outbound `sdcodex:gallery-sources`
  (`{activeSourceId,sources}`) message to `window.parent`; outside an iframe it
  also renders the source rail. Sources are switched by setting `?source=&album=`
  and reloading via `location.assign`.
- `updateFolderHistory` — the folder state is carried in the `?album=` query
  parameter (`pushState` / `replaceState` with the state key `folderFrameAlbum`);
  the `popstate` handler re-navigates when `?album` differs.
- `setupEventListeners` — the single wiring entry point (called after
  `loadConfiguration`, `loadOptimizeCapability` and `loadCaptionCapability` on
  `DOMContentLoaded`); it owns every click / key / fullscreen / touch / scroll /
  visibility listener. `startAutoRefreshTimer` owns the polling interval.
- Forked endpoint contract — all server calls in this copy use the `/betacaption`
  prefix:
  - `immichOriginalUrl` → `/betacaption/gallery/api/immich/<sid>/original/<album><file>`
  - `OPTIMIZE_ENDPOINT` → `/betacaption/gallery/api/optimize`
  - `CONVERT_ENDPOINT` → `/betacaption/gallery/api/convert`
  - `loadOptimizeCapability` → `/betacaption/gallery/api/optimize-status`
  - `loadConfiguration` → `/betacaption/gallery/api/folderframe.config.json`
  - `loadCaptionCapability` → `/betacaption/api/status` and plugin id `betacaption`
  - `captionCurrentImage` → `/betacaption/gallery/api/caption-target`,
    `/betacaption/api/check-connection`, `/betacaption/api/caption-single`
  - `loadMediaMetadata` → `/betacaption/gallery/api/meta` and
    `/betacaption/gallery/api/immich/<sid>/meta`
  - `downloadCurrentWorkflow` → `/betacaption/gallery/api/workflow`
  - `loadHeicDecoder` → `/betacaption/gallery/api/legacy-ui/heic2any.min.js`
- `immichSourceId` parses the server id with `/\/gallery\/api\/immich\/([A-Za-z0-9_-]+)\//`
  against the source URL (prefix-agnostic, so it still matches
  `/betacaption/gallery/api/immich/<id>/`); `isRemoteSource` is true exactly when
  that id is present.
- `isManifestOnlySource` (`discoveryMode === 'manifest'`) and
  `usesPublishedManifest` (`discoveryMode !== 'directory' && manifestUrl`) gate
  the published-index code path; `getImagePool` lazily builds the HEIC/quicktime
  image pool used by `getSpecialImageURL`.
- Grid virtualization contract — `gridVirtualizer = {start, end, jumpToStart(),
  jumpToEnd(), update()}` and the per-session `session.appendTiles(previousLength, newLength)`
  used by progressive publishing.
- `loadGallery({preserveView, forceCacheClear, silent})` is the single entry point
  that returns `true` on success, `false` on a handled missing-folder / manifest
  failure, or `undefined` when superseded / aborted.
- Bootstrap — the `DOMContentLoaded` handler runs `loadConfiguration` →
  `loadOptimizeCapability` → `loadCaptionCapability` → `setupEventListeners` →
  `updateControlStates` → `updateFullscreenButton` → `loadGallery` →
  `updateFolderHistory` → `updateGalleryHeaderLayout` → `startAutoRefreshTimer`.
- Pure-ish helpers — `detectContainer` (sniffs
  jpeg / png / webp / gif / avif / heic / quicktime / unknown from magic bytes),
  `formatBytes`, `compareFilenames` (numeric, base-insensitive, URL-decoded) and
  `escapeHtml` (`&`, `<`, `>`, `"`, `'`).

### `settings.js` (identical to the canonical copy)

- Exported object (global `window.FolderFrameSettings`, or `module.exports` under
  Node) — **exactly**
  `{normalizeConfig, resolveSettings, directoryUrl, mediaUrl, relativeMediaPath,
  listingEntry, thumbnailUrl}`. `DEFAULTS`, `GRID_DENSITIES`, `BOOLEAN_KEYS`,
  `SAVED_KEYS`, `INTERVALS`, `object`, `normalizeAlbum`, `validateSettings`,
  `applyLayer` and `urlSettings` are module-private.
- `normalizeConfig(raw, pageUrl)` → `{baseUrl, sources[], defaults, index, embed}`;
  each source becomes
  `{id, label, path, url, thumbnailPath, thumbnailUrl, manifestPath, manifestUrl, scanCache, discoveryMode}`.
- `resolveSettings(config, search, readStored)` →
  `{settings, profile, source, preferenceKey, warnings}`; the search string
  supports `profile=index|embed` plus the URL aliases `source`, `album`, `view`,
  `sort`, `interval`, `imageMode`, `shuffle`, `autorefresh`, `tv`, `autoplay`,
  `remember`, `controls`, `showFilenames`, `download`, `copy`, `buttonLabels`,
  `density`.
- `directoryUrl` / `mediaUrl` / `thumbnailUrl` are the only sanctioned URL
  builders (album-relative directory URL, encoded media URL, `.webp` thumbnail
  URL derived from the `thumbnailUrl` base).

### `resilience.js` (identical to the canonical copy)

- Exported object (global `window.FolderFrameResilience`, or `module.exports`
  under Node) — **exactly**
  `{request, createTaskQueue, createImagePool, abortError, timeoutError, httpError}`;
  `httpErrorDetailed` is private, so `httpError` stays a plain `HTTP <status>`
  error while `request()` throws the detailed variant.
- `request(url, {signal, timeout=15000, body='text', ...fetchOptions})` resolves
  the response body via `response[body]()` (`text` | `json` | `arrayBuffer` |
  `blob`) and rejects with the named errors `AbortError`, `TimeoutError` or
  `HTTPError` (carrying `.status`, `.url` and `.detail`).
- `createTaskQueue({concurrency=4})` →
  `{schedule(task, {signal, priority=0}) -> Promise, stats() -> {active, queued, concurrency}}`.
- `createImagePool({download, decode, thumbnail, createURL, revokeURL, warn,
  concurrency=2, decodeTimeout=30000, grace=250, limits})` →
  `{acquire(file, kind='viewer', signal) -> Promise<{url, release()}>,
  invalidate(file), stats() -> {active, jobs, viewer, thumbnail}}`.

### `folderframe.config.json` (identical to the canonical copy)

- Exactly four top-level keys: `sources` (a non-empty array; omitted ⇒ the
  single `{id:'photos',label:'Photos',path:'photos/'}`), `defaults`, `index` and
  `embed`.
- Source object keys: `id`, `label`, `path`, `discoveryMode`, plus the optional
  `thumbnailPath`, `manifestPath` and `scanCache`.
- The layer keys are the settings allow-list: `source`, `album`, `view`, `sort`,
  `interval`, `imageMode`, `shuffle`, `autoRefresh`, `refreshInterval`,
  `tvMode`, `autoplay`, `rememberPreferences`, `controls`, `showFilenames`,
  `showDownloadButton`, `showCopyButton`, `showButtonLabels`, `gridDensity`.
- The shipped values are source id `photos`, `defaults.view` `'folders'`,
  `defaults.sort` `'filename'`, `defaults.interval` 5,
  `defaults.gridDensity` `'comfortable'`, `index.refreshInterval` 120 and
  `embed.refreshInterval` 300.

## Invariants

- `resilience.js:request` — one `AbortController` per call, a single deadline
  that also covers body consumption, the timer cleared and the abort listener
  removed in `finally`; an already-aborted caller signal rejects immediately and
  late completions are ignored.
- `resilience.js:createTaskQueue` — the concurrency must be a positive integer
  or it throws; dispatch order is priority descending then submission order
  ascending; aborting a still-queued item removes it and rejects with
  `AbortError`; `stats()` always reports the concurrency.
- `resilience.js:createImagePool` — at most `concurrency` (default 2) jobs run;
  the default limits are viewer `[32 entries, 64 MiB]` and thumbnail
  `[128 entries, 16 MiB]`; the decode-stall deadline of 30000 ms keeps the slot
  occupied until the job settles; orphaned queued jobs are reaped after the
  250 ms grace; eviction is oldest-used-first and skips entries with `refs > 0`;
  stale entries are revoked only when `refs` reaches 0; a timed-out job rejects
  every consumer with a `TimeoutError`.
- `settings.js:validateSettings` — strict allow-lists: `view` ∈ {all,folders},
  `sort` ∈ {newest,oldest,filename}, `imageMode` ∈ {fit,original},
  `gridDensity` ∈ {compact,comfortable,spacious}, `interval` ∈
  `INTERVALS` `[3,5,10,15,30,60,300,900,3600]`, `refreshInterval` an integer
  1..86400, booleans must be `typeof boolean`, `source` must match a configured
  source id, and any unknown key throws.
- `settings.js:normalizeAlbum` — rejects non-strings, backslashes, control chars
  `\x00-\x1f` and any `.` or `..` segment (the album cannot escape its source);
  `settings.js:mediaUrl` rejects empty filenames, `/` or `\` and `.` or `..`.
- `settings.js:normalizeConfig` — source ids must be unique and match
  `^[a-zA-Z0-9_-]+$`, labels must be non-blank, paths must resolve to http(s)
  with no username / password / search / hash and are normalized to a trailing
  slash, `manifestPath` must additionally end in `.json`, `scanCache` must be
  boolean, `discoveryMode` ∈ {auto,directory,manifest} and `manifest` requires
  `manifestPath`; unknown top-level sections throw.
- `settings.js:listingEntry` — returns `null` unless the href is a same-origin
  direct child of the requested directory: query / fragment links, `?` / `#`
  hrefs, foreign origins and paths outside `base.pathname` are rejected, and
  names containing `/`, `\` or control chars or equal to `.` / `..` are dropped.
- `settings.js:thumbnailUrl` — returns `null` when the source has no
  `thumbnailUrl` or when the relative path is empty or starts with `../`.
- `settings.js:resolveSettings` — the profile defaults to `index` unless
  `profile=embed`; `embed` starts with `refreshInterval` 300 and
  `rememberPreferences` false while `index` starts at 120 / true; a
  published-manifest source (`discoveryMode !== 'directory' && manifestUrl`)
  forces `autoRefresh` false unless `defaults` or the active profile explicitly
  set `autoRefresh` or `tvMode`; only `SAVED_KEYS` are read back from storage;
  the legacy `gallery.preferences` key is migrated only for profile `index` +
  source id `photos` + the default photos URL; URL overrides always win last.
- `settings.js:applyLayer` — `tvMode === true` expands to the preset
  `{imageMode:'fit', shuffle:true, autoRefresh:true, autoplay:true}` in the same
  layer, but explicit fields in that layer still take precedence.
- `app.js:isIgnoredDirectoryName` / `app.js:isIgnoredFileName` — hidden / OS
  directories (plus any `.trash-*` prefix) and dot-files, `~$` temp files and the
  `.tmp/.part/.partial/.crdownload/.download/.bak/.old` suffixes are excluded
  from listings and manifest records.
- `app.js:scanDirectory` — when a sentinel from `IGNORE_SENTINELS` is present
  the whole listing is voided (files and folders cleared, `ignored=true`);
  results are sorted with `localeCompare` numeric / base and cached only when
  `activeSource.scanCache` is true and the directory `Last-Modified` matched.
- `app.js:scanDirectoryRecursive` — a bounded breadth-first frontier with at
  most `SCAN_SIBLING_CONCURRENCY` (5) listings in flight, no parent-awaits-children
  chain (deadlock-free), visited-set de-duplication, per-top-subtree
  `onTopComplete` accounting, and late results discarded once the scan has settled.
- `app.js:loadGallery` — aborts any previous `scanSession` and only mutates state
  while `current()` (same session, not aborted); progressive publishing is only
  for mode `'all'` in grid view and is throttled to ≥400 new files or ≥2000 ms
  between publishes; files from `failedFolders` are preserved rather than
  removed; a missing top-level album (404 / 410) goes to `handleMissingFolder`;
  manifest errors on a manifest-only source show the "Reload Library" notice
  instead of a generic failure.
- `app.js:trimDateCache` — entries are dropped when `checked` is missing /
  non-finite / in the future, older than `DATE_CACHE_TTL` (24 h) or have a
  non-finite date, and the cache is trimmed oldest-first to `DATE_CACHE_LIMIT`
  (2000) entries; `loadDateCache` / `saveDateCache` only keep URLs that start
  with `activeSource.url`.
- `app.js:loadDateCache` / `app.js:getScanManifest` — the storage key includes
  `baseUrl` + source id + source URL, so the preferences, date cache and scan
  manifest never leak across sources.
- `app.js:saveScanManifest` — writes only when `activeSource.scanCache`, capped
  at `SCAN_MANIFEST_DIRECTORY_LIMIT` (5000) directories sorted by most recently
  checked; quota / JSON errors are swallowed.
- `app.js:findAlbumCover` — at most `ALBUM_COVER_MAX_LISTINGS` (12) directory
  listings and `ALBUM_COVER_MAX_DEPTH` (4) levels of recursion, skipping
  already-visited folders, with the listing cache shared via
  `albumPreviewSession.listingCache`; `confirmedEmpty` is only returned when no
  media and no truncated search were seen.
- `app.js:startAlbumPreviews` — runs at most 3 concurrent cover loads and
  observes tiles with an `IntersectionObserver` (`rootMargin` 300 px), aborting
  offscreen items; `app.js:queueVideoThumbnail` has a fixed
  `VIDEO_THUMBNAIL_TIMEOUT` of 8000 ms and clears the source on failure / abort.
- `app.js:sortMediaFiles` — the filename mode is a pure `localeCompare`
  (numeric, base); the date modes run at most 4 concurrent HEAD requests under a
  single 8000 ms abort deadline, reuse cached dates younger than
  `DATE_CACHE_TTL` unless `refreshDates` is set, and sort files without dates
  last, tie-broken by `compareFilenames`.
- `app.js:applyGridDensity` — only `compact|comfortable|spacious` are accepted
  (`GRID_DENSITY_PX` 130 / 180 / 240 px); anything else falls back to
  `comfortable` and writes `--grid-tile-min`.
- `app.js:cycleSort` — cycles newest → oldest → filename and refuses while
  `isScanning`; `app.js:cycleGridDensity` cycles compact → comfortable →
  spacious with a pure re-layout (no rescan).
- `app.js:validateManifestRecord` — `record.path` must equal the expected path,
  files must be direct children (`parentFolder(path) === expectedPath`) and
  media-typed, folder names must be non-empty and free of `/`, `\` or control
  chars or `.` / `..`; ignored names are filtered, and any malformation
  invalidates the whole record.
- `app.js:safeManifestPath` — rejects non-strings, backslashes, control chars
  and `.` / `..` segments; `app.js:loadPersistentChunk` requires a chunk URL that
  stays same-origin and under the manifest base path with no query / hash;
  `app.js:ensurePersistentManifest` requires
  `index.version === PERSISTENT_MANIFEST_VERSION` (1) with a valid root record
  and memoizes an `unavailable` failure for the rest of the scan (thrown for
  manifest-only sources, `null` fallback otherwise).
- `app.js:updateGridView` — only appends DOM tiles when `appendTiles` exists,
  the folder / mode match the current session, and every already-rendered index
  is byte-identical between the old and new `mediaFiles` arrays; any divergence
  falls back to a full `renderGridView`.
- `app.js:renderGridView` — virtualization kicks in above `GRID_BATCH_SIZE` (100)
  rendered tiles, the window is `GRID_WINDOW_SIZE` (300), the load margin is
  300 px, and the column math uses scale 0.667 ≤560 px / 0.778 ≤900 px / 1 above
  with gap 12 or 18 px (must agree with the `styles.css` breakpoints).
- `app.js:openConvertPrompt` / `app.js:runConvert` — only one Optimize / Convert
  may run (`operationInFlight`) and prompts are refused while `isScanning`;
  auto-refresh is suspended while `operationInFlight` so a mid-job rescan cannot
  hide the busy state.
- `app.js:handleWheel` / `app.js:handleTouchMove` — zoom is clamped to 0.1..10 in
  original mode and 1..10 in fit mode; the pan resets at 1× in fit mode.
- `app.js:handleTouchEnd` — a swipe dismiss requires a vertical-axis gesture of at
  least `min(180, max(100, 22% of viewport height))` or a fast flick (≥60 px,
  ≥0.75 px/ms, ≥40 ms); horizontal navigation requires `|dx| >= 50` and
  `|dx| > 1.5*|dy|`; a tap travelling > 6 px does not dismiss
  (`app.js:handleViewerDismissClick`).
- `app.js:resetIdleTimer` — the chrome hides after 3000 ms of idle (1800 ms in TV
  mode) and `hideUI` is suppressed while dragging, pinching, failed, in grid
  view, or when the focus is visibly inside the toolbar / arrows / details panel.
- `app.js:scheduleErrorAdvance` — a failed media item auto-advances after exactly
  3000 ms and only if the slideshow is still playing and `mediaLoadId` has not changed.
- `app.js:imageClipboardAvailable` — requires `window.isSecureContext`,
  `navigator.clipboard.write` and a defined `ClipboardItem`;
  `app.js:getSpecialImageURL` releases its pool lease (and throws `AbortError`)
  when the caller signal is already aborted.
- `app.js:loadConfiguration` — aborts the config fetch after 8000 ms and falls
  back to `settingsApi.normalizeConfig({}, location.href)` with a visible warning
  rather than failing boot; `app.js:loadCaptionCapability` treats a non-ok status
  as "not installed" and only un-hides the caption section when it is.
- `app.js:detectContainer` / `app.js:makeThumbnail` — HEIC/quicktime
  reclassification is only raised for the ISO-BMFF brands `mif1`/`heic`/… or
  `qt`/`isom`/…; thumbnails are scaled to a 480 px longest edge and encoded as
  JPEG quality 0.8.
- `app.js:ensureStarredSet` / `app.js:saveStarredSet` — stars are keyed by
  `settingsApi.relativeMediaPath` and persisted with `STARRED_STORAGE_VERSION` 1;
  malformed storage is ignored rather than thrown.
- `app.js:updateMediaActions` — caption actions are only offered for local
  (non-Immich) still images and only when `captionCapable` is true; Optimize /
  Convert are hidden and disabled for remote sources.

## Side Effects

- `app.js:$` — extensive DOM reads / writes on load and per interaction: an
  element-binding block for ~90 ids, `innerHTML` replacement in
  `app.js:renderGridView` and `app.js:renderBreadcrumb`, and
  `classList` / `aria-pressed` / `aria-busy` / `aria-valuenow` toggles in
  `app.js:updateControlStates`, `app.js:showUI` / `app.js:hideUI`,
  `app.js:applyTransform`, `app.js:setScanProgressBar`, plus `style.display` and
  the body-level classes `has-source-rail`, `hide-filenames`,
  `hide-viewer-button-labels`, `controls-free`, `cursor-hidden` and `viewer-open`
  in `app.js:renderSourceRail`, `app.js:syncViewerModal` and
  `app.js:loadConfiguration`.
- `app.js:loadConfiguration` / `app.js:loadOptimizeCapability` /
  `app.js:loadCaptionCapability` / `app.js:scanDirectory` /
  `app.js:directoryModifiedTime` / `app.js:ensurePersistentManifest` /
  `app.js:loadPersistentChunk` / `app.js:sortMediaFiles` /
  `app.js:renderGridView` — network calls (`fetch` / `resilience.request`):
  config, optimize-status, caption status, `/api/plugins`, directory listings,
  the HEAD `Last-Modified`, HEAD existence probes, the manifest index / chunks,
  and the media / thumbnail loads scheduled by `app.js:queueNativeImageSource`,
  `app.js:queueVideoThumbnail` and `app.js:getImagePool`. All server routes in
  this copy are under `/betacaption` plus the core `/api/plugins` probe.
- `app.js:requestOptimization` / `app.js:requestConvert` /
  `app.js:captionCurrentImage` / `app.js:downloadCurrentWorkflow` — POST bodies
  to the optimize, convert, check-connection and caption-single endpoints (the
  convert / optimize calls attach an `Authorization: Bearer` header read from
  `localStorage.civitaiApiKey`) and anchor-click downloads of the workflow URL.
- `app.js:getScanManifest` / `app.js:saveScanManifest` / `app.js:loadDateCache` /
  `app.js:saveDateCache` / `app.js:savePreferences` / `app.js:ensureStarredSet` /
  `app.js:saveStarredSet` / `app.js:requestOptimization` /
  `app.js:requestConvert` / `app.js:captionCurrentImage` /
  `app.js:loadConfiguration` — `localStorage` access under the keys
  `folderframe.scan-manifest:v2:*`, `folderframe.date-cache:v1:*`,
  `folderframe.preferences:*`, `folderframe.starred`, `civitaiApiKey`,
  `captionLmStudioUrl`, `captionPrompt`, `captionTriggerTag` and `captionModel`.
- `app.js:startGridSession` / `app.js:startAlbumPreviews` / `app.js:showMedia` /
  `app.js:stopViewerSession` / `app.js:directoryModifiedTime` /
  `app.js:scanDirectoryRecursive` / `app.js:loadGallery` /
  `app.js:findAlbumCover` — browser APIs: `AbortController`, `IntersectionObserver`,
  `requestAnimationFrame`, `DOMParser`, `URL` / `URLSearchParams`,
  `history.pushState` / `replaceState` and `location.assign`.
- `app.js:getImagePool` / `app.js:makeThumbnail` / `app.js:imageClipboardBlob` /
  `app.js:copyCurrentImage` / `app.js:copyCurrentFilename` /
  `app.js:loadHeicDecoder` — `URL.createObjectURL` / `revokeObjectURL`, canvas 2d
  + `toBlob`, `navigator.clipboard.write` / `writeText` with `ClipboardItem` and a
  `document.execCommand('copy')` textarea fallback, and the dynamic injection of
  a `<script>` for `heic2any.min.js`.
- `app.js:toggleFullscreen` / `app.js:toggleTvMode` /
  `app.js:handleFullscreenChange` — the `Element.requestFullscreen` /
  `document.exitFullscreen` API and a `fullscreenchange` listener;
  `app.js:startAutoRefreshTimer` and `app.js:scheduleErrorAdvance` use
  `setInterval` / `setTimeout`, and `app.js:setupEventListeners` also reacts to
  `visibilitychange`, `resize`, `scroll` (passive) and a global `keydown`
  shortcut handler.
- `app.js:console` logging — `console.info` for manifest-load and fullscreen
  refusals, `console.warn` for settings warnings and optimize / convert / cache
  failures, `console.error` for scan and HEIC / metadata failures.
- `app.js:performance.now()` timing for the swipe-gesture velocity and the
  slideshow progress (`app.js:handleTouchEnd`, `app.js:startSlideshowTimer`).
- `app.js:downloadCurrentWorkflow` — creates a temporary `<a download>` pointing
  at the workflow endpoint, clicks it, then removes it.
- `settings.js:api` / `resilience.js:api` — both files attach exactly one global
  (`window.FolderFrameSettings` / `window.FolderFrameResilience`) when
  `module.exports` is unavailable, otherwise they write to `module.exports`;
  neither performs `fetch`, storage or DOM access itself.
- `app.js:loadDateCache` / `app.js:getScanManifest` / `app.js:loadConfiguration` /
  `app.js:startAutoRefreshTimer` — read-only storage / scheduling side effects
  that must be tolerated when `localStorage` throws (private mode); the errors
  are swallowed so sorting, scanning and boot still work.

## Verification

- Run: `<test-command>`
