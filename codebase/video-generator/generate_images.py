"""Optional image generation stage; disabled for this prototype."""


def generate_images(scenes, client, enabled=False):
    if not enabled:
        return {"enabled": False, "images": []}
    raise RuntimeError("Image generation is intentionally disabled in this prototype")
