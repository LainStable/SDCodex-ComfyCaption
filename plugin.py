"""SDCodex ComfyCaption plugin entrypoint."""

import os
import shutil
import sys

plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)


def init_plugin(app, db, plugin_info=None):
    """Register caption_bp and models_bp blueprints, install ComfyUI nodes."""
    from caption_backend import caption_bp
    from caption_models_backend import models_bp

    if "caption_bp" not in app.blueprints:
        app.register_blueprint(caption_bp)
        app.logger.info("ComfyCaption API mounted at /comfy-caption/api")

    if "caption_models_bp" not in app.blueprints:
        app.register_blueprint(models_bp)
        app.logger.info("ComfyCaption Models API mounted at /comfy-caption/models")

    # Install / sync ComfyUI custom nodes into the configured custom-nodes folder.
    src_nodes = os.path.join(plugin_dir, "comfyui-sdcodex")
    if os.path.isdir(src_nodes):
        custom_nodes_dirs = [
            os.environ.get("COMFYUI_CUSTOM_NODES"),
            os.environ.get("COMFY_CUSTOM_NODES"),
            "/data/custom_nodes",
            "/data/comfyui_custom_nodes",
        ]
        for cdir in custom_nodes_dirs:
            if cdir and os.path.isdir(cdir):
                dest = os.path.join(cdir, "comfyui-sdcodex")
                try:
                    shutil.copytree(src_nodes, dest, dirs_exist_ok=True)
                    app.logger.info("Installed/updated ComfyUI custom nodes to %s", dest)
                except Exception as err:
                    app.logger.warning("Could not copy ComfyUI nodes to %s: %s", dest, err)
                break

    return True
