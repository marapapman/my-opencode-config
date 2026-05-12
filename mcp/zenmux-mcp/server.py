#!/usr/bin/env python3
"""
MCP Server for Zenmux AI Image Generation & Editing API.

Tools:
  - zenmux_generate_image : Generate images from text prompts
  - zenmux_edit_images    : Edit/combine existing images
"""

import os
import json
import base64
import mimetypes
import asyncio
import time
from pathlib import Path
from typing import Optional, List

import httpx
from pydantic import BaseModel, Field, ConfigDict, field_validator
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("zenmux_mcp")

API_BASE_URL = "https://zenmux.ai/api/v1"
API_KEY = os.environ.get("ZENMUX_API_KEY", "")
DEFAULT_SAVE_DIR = os.environ.get("ZENMUX_IMAGE_DIR", "/tmp/opencode/zenmux-images")
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.ReadError,
    httpx.TimeoutException,
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {API_KEY}"}


def _handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        detail = ""
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:500]
        if status == 401:
            return "Error: Invalid API key. Set ZENMUX_API_KEY environment variable."
        if status == 429:
            return "Error: Rate limit exceeded. Please wait and retry."
        return f"Error: API returned {status} — {detail}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    return f"Error: {type(e).__name__}: {e}"


async def _post_with_retries(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    for attempt in range(3):
        try:
            resp = await client.post(url, **kwargs)
            if resp.status_code in {408, 425, 429, 500, 502, 503, 504} and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            return resp
        except RETRYABLE_EXCEPTIONS as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError("request failed after retries")


def _save_b64_images(data: list, save_dir: str) -> list:
    saved = []
    out = Path(save_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(data):
        b64 = item.get("b64_json") or item.get("b64")
        url = item.get("url")
        ext = ".png"
        if b64:
            raw = base64.b64decode(b64)
            fpath = out / f"generated_{int(time.time())}_{i + 1}{ext}"
            fpath.write_bytes(raw)
            saved.append(str(fpath))
        elif url:
            saved.append(url)
        else:
            saved.append(f"<no image data for index {i}>")
    return saved


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class GenerateImageInput(BaseModel):
    """Input for generating images from a text prompt."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    prompt: str = Field(
        ...,
        description="Text description of the image to generate",
        min_length=1,
        max_length=4000,
    )
    model: str = Field(
        default="openai/gpt-image-2",
        description="Model name (e.g. 'openai/gpt-image-2')",
    )
    n: int = Field(
        default=1,
        description="Number of images to generate",
        ge=1,
        le=4,
    )
    size: str = Field(
        default="1024x1024",
        description="Image size, such as 1024x1024, 1536x1024, 1024x1536, or any supported WIDTHxHEIGHT",
    )
    save_to: Optional[str] = Field(
        default=None,
        description="Optional directory path to save generated images locally",
    )

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: str) -> str:
        if v == "auto":
            return v
        parts = v.lower().split("x")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("size must be WIDTHxHEIGHT, for example 1024x1024")
        width, height = (int(part) for part in parts)
        if width <= 0 or height <= 0 or width % 16 != 0 or height % 16 != 0:
            raise ValueError("width and height must be positive multiples of 16")
        ratio = width / height
        if ratio < 1 / 3 or ratio > 3:
            raise ValueError("aspect ratio must be between 1:3 and 3:1")
        return v


class EditImagesInput(BaseModel):
    """Input for editing images."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    prompt: str = Field(
        ...,
        description="Instruction describing the desired edit (e.g. 'Create a lovely gift basket with these items')",
        min_length=1,
        max_length=4000,
    )
    images: List[str] = Field(
        ...,
        description="Local file paths of images to edit (1–4 images)",
        min_length=1,
        max_length=4,
    )
    model: str = Field(
        default="openai/gpt-image-2",
        description="Model name",
    )
    save_to: Optional[str] = Field(
        default=None,
        description="Optional directory path to save the resulting image",
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, v: List[str]) -> List[str]:
        for path in v:
            if not os.path.isfile(path):
                raise ValueError(f"Image file not found: {path}")
        return v


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="zenmux_generate_image",
    annotations={
        "title": "Generate Image with AI",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def zenmux_generate_image(params: GenerateImageInput) -> str:
    """Generate images from a text prompt using the Zenmux AI API.

    Use this tool when you need to create an image from a text description.
    Returns URLs or local file paths for the generated images.

    Args:
        params: GenerateImageInput with prompt, model, n, size, save_to

    Returns:
        JSON string with generated image information
    """
    if not API_KEY:
        return "Error: ZENMUX_API_KEY environment variable is not set."

    payload = {
        "model": params.model,
        "prompt": params.prompt,
        "n": params.n,
        "size": params.size,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await _post_with_retries(
                client,
                f"{API_BASE_URL}/images/generations",
                headers={**_auth_headers(), "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            body = resp.json()
    except Exception as e:
        return _handle_error(e)

    data = body.get("data", [])
    if not data:
        return "Error: API returned no image data."

    result = {"model": params.model, "images": []}

    save_dir = params.save_to or DEFAULT_SAVE_DIR
    if save_dir:
        saved = _save_b64_images(data, save_dir)
        result["saved_to"] = save_dir
        result["images"] = [
            {"index": i, "path": p} for i, p in enumerate(saved)
        ]
    else:
        for i, item in enumerate(data):
            entry = {"index": i}
            if item.get("url"):
                entry["url"] = item["url"]
            if item.get("b64_json"):
                entry["b64_preview"] = item["b64_json"][:80] + "..."
            elif item.get("b64"):
                entry["b64_preview"] = item["b64"][:80] + "..."
            result["images"].append(entry)

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="zenmux_edit_images",
    annotations={
        "title": "Edit or Combine Images with AI",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def zenmux_edit_images(params: EditImagesInput) -> str:
    """Edit or combine existing images using AI, guided by a text prompt.

    Upload 1–4 local image files along with a text instruction and the API
    returns a new image.  Useful for style transfer, object insertion/removal,
    scene composition, background replacement, etc.

    Args:
        params: EditImagesInput with prompt, images, model, save_to

    Returns:
        JSON string with the result image information
    """
    if not API_KEY:
        return "Error: ZENMUX_API_KEY environment variable is not set."

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = []
            for img_path in params.images:
                mime, _ = mimetypes.guess_type(img_path)
                if mime is None:
                    mime = "image/png"
                filename = os.path.basename(img_path)
                content = Path(img_path).read_bytes()
                files.append(
                    ("image[]", (filename, content, mime))
                )

            data = {
                "model": params.model,
                "prompt": params.prompt,
            }
            resp = await _post_with_retries(
                client,
                f"{API_BASE_URL}/images/edits",
                headers=_auth_headers(),
                data=data,
                files=files,
            )
            resp.raise_for_status()
            body = resp.json()
    except Exception as e:
        return _handle_error(e)

    result_data = body.get("data", [])
    if not result_data:
        return "Error: API returned no image data."

    result = {"model": params.model, "images": []}

    if params.save_to:
        saved = _save_b64_images(result_data, params.save_to)
        result["saved_to"] = params.save_to
        result["images"] = [
            {"index": i, "path": p} for i, p in enumerate(saved)
        ]
    else:
        for i, item in enumerate(result_data):
            entry = {"index": i}
            if item.get("url"):
                entry["url"] = item["url"]
            if item.get("b64_json") or item.get("b64"):
                b64 = item.get("b64_json") or item.get("b64")
                entry["b64_preview"] = b64[:80] + "..."
            result["images"].append(entry)

    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
