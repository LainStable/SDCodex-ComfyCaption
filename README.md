# SDCodex-ComfyCaption

## Captioning studio

The plugin page is split in two: the **left third** holds the image panel, the
SD-prompt inspector and the caption editor, and the **right two thirds** are a
full Gallery browser (grid, folder rail, thumbnails, viewer) served by the
plugin itself — the Gallery plugin does not have to be installed. Clicking an
image in the browser loads it into the panel.

The media root comes from the environment: `CAPTION_ROOT`, falling back to
`GALLERY_ROOT` (and then `/data/downloads`). There is no folder bar in the
studio — change the volume mapping to point at a different tree. Saved, named
prompt presets (localStorage, per browser) sit next to the system prompt field,
and a running batch can be paused or cancelled from the task notification.

## Install the ComfyUI node pack

Open the plugin's **Caption Models** settings page, enter the ComfyUI installation
directory, and select **Set Directory**. Once validated, select **Install Nodes**
to copy the bundled `comfyui-sdcodex` pack into
`<ComfyUI directory>/custom_nodes/comfyui-sdcodex`. Existing files in that node
pack directory are updated in place; unrelated custom nodes are left untouched.
Restart ComfyUI after installing or updating the pack.

In a local SDCodex installation, enter the ComfyUI path as seen by the local
backend process. In Docker mode, mount the ComfyUI installation directory into
the SDCodex container and enter its **container path**. The default plugin
volume maps `./comfyui` to `/data/comfyui`; change that host path to your actual
ComfyUI installation if needed. The selected folder must contain `main.py`.
Only signed-in administrators can save the target directory or install nodes.
Directory selection and node installation are explicit; installing the plugin
does not write into ComfyUI until an administrator selects **Install Nodes**.