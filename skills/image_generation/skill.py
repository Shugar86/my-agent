import os, base64
from openai import OpenAI


def generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard",
                    n: int = 1, output_dir: str = "output") -> dict:
    try:
        client = OpenAI()
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
            response_format="b64_json",
        )
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for i, img_data in enumerate(resp.data):
            path = os.path.join(output_dir, f"generated_{i}_{hash(prompt) % 10000}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_data.b64_json))
            paths.append(path)
        return {"paths": paths, "prompt": prompt, "revised_prompt": resp.data[0].revised_prompt}
    except Exception as e:
        return {"error": str(e)}


def generate_image_variation(image_path: str, n: int = 1, size: str = "1024x1024") -> dict:
    try:
        client = OpenAI()
        with open(image_path, "rb") as f:
            resp = client.images.create_variation(
                image=f,
                n=n,
                size=size,
                response_format="b64_json",
            )
        paths = []
        os.makedirs("output", exist_ok=True)
        for i, img_data in enumerate(resp.data):
            path = f"output/variation_{i}_{hash(image_path) % 10000}.png"
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_data.b64_json))
            paths.append(path)
        return {"paths": paths}
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="generate_image",
        description="Generate an image from a text prompt using DALL-E 3. Saves to output/ directory.",
        parameters={"type": "object", "properties": {
            "prompt": {"type": "string"},
            "size": {"type": "string"},
            "quality": {"type": "string"},
        }},
        execute_fn=lambda prompt="", size="1024x1024", quality="standard":
            generate_image(prompt, size, quality),
    )
    registry.register(
        name="generate_image_variation",
        description="Create a variation of an existing image using DALL-E 3.",
        parameters={"type": "object", "properties": {
            "image_path": {"type": "string"},
        }},
        execute_fn=lambda image_path="": generate_image_variation(image_path),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["generate_image", "generate_image_variation"]:
        registry.unregister(name)
