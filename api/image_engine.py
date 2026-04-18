"""
Image Forensic Engine for PREE
Detects AI-generated images using Gemini Vision, EXIF metadata analysis,
and pixel-level heuristics.
"""

import base64
import io
import json
import logging
import os
import re
import struct
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("engine")

# ---------------------------------------------------------------------------
# System prompt for Gemini Vision — image forensics
# ---------------------------------------------------------------------------
IMAGE_FORENSIC_PROMPT = """\
ROLE:
You are the Visual Forensic Analyzer and Prompt Reverse Engineer within PREE. You are an elite, world-class expert in digital image forensics, CGI detection, and AI generative models.
Your TWO objectives are:
  A) Determine whether an image was created by an AI generator or by a human with unparalleled accuracy.
  B) If AI-generated, reverse-engineer the most likely prompt that produced it with extreme detail.

FORENSIC METHODOLOGY — Look extremely closely, pixel-by-pixel, and score each dimension 0-100:
1. **Anatomy Score**: Check human subjects meticulously for micro-errors: asymmetric pupils, inconsistent iris reflections, non-euclidean limbs, fused teeth, missing/blended finger joints, hair-skin boundary blending, anomalous fabric blending.
   Score 0 = scientifically perfect anatomy, 100 = severe anatomical impossibilities.
2. **Text Score**: Look for "alien glyphs", garbled text, nonsensical background signage, impossible letter forms, inconsistent fonts on the same plane, kerning destruction.
   Score 0 = all text is perfectly legible and structurally correct, 100 = text is fully generative noise.
3. **Texture Score**: Detect implicit sub-pixel patterns, repeating noise textures, over-smoothed skin (plastic effect), hyper-sharp focus planes with no depth-of-field transition, visible Voronoi tiling, or aberrant material specular highlights.
   Score 0 = fully natural textures, 100 = completely synthetic textures.
4. **Lighting Score**: Identify impossible shadow casting, inconsistent light source angles, physically implausible multi-point reflections (especially in eyes or metal), global illumination bleeding, or flat volumetric lighting.
   Score 0 = physically perfect global illumination, 100 = highly impossible lighting geometry.
5. **Style Score**: Identify hyper-specific AI generator aesthetics — e.g., Midjourney v6 cinematic grading and bokeh bias, DALL·E 3 plastic illustration and extreme prompt adherence, Stable Diffusion XL color banding and specific VAE desaturation, Flux hyper-detailed skin pores, Imagen photorealism flaws.
   Score 0 = unidentifiable/human origin, 100 = undeniable generator-specific signature.
6. **Watermark Score**: Heavily penalize visible artifact watermarks, SynthID hidden noise structures, crop-marks, edge-of-frame signatures, or recognizable generator app UI remnants.
   Score 0 = no watermark signals, 100 = unmistakable AI watermark detected.

PROMPT RECONSTRUCTION (if AI-generated):
- Analyze the subject, composition (Golden Ratio, Rule of Thirds bias), specific lighting ("Rembrandt lighting", "volumetric", "Octane Render"), camera and lens parameters ("shot on 35mm f/1.8", "isometric 3D"), color grading, and precise style keywords.
- Reconstruct the *exact*, highly optimized master prompt used, incorporating technical photography terms that AI generators respond to.
- List suspected negative prompts.
- If the image appears human-made, set reconstructed_prompt to "N/A — Image appears to be of authentic human origin after rigorous analysis."

OUTPUT FORMAT:
Return ONLY a valid JSON object. No markdown.
{
  "analysis": {
    "origin_verdict": "AI_GENERATED | LIKELY_HUMAN | INCONCLUSIVE",
    "confidence_score": "Integer 0-100 (Must reflect extreme rigor)",
    "suspected_generator": "Specific version (e.g., midjourney v6, dall-e 3, sd-xl, flux dev, unknown)",
    "detected_anomalies": ["Array of highly specific, granular technical anomalies found (e.g. 'Specular highlight in left pupil differs by 15deg from main light source')"],
    "style_markers": ["Array of hyper-specific stylistic observations"]
  },
  "confidence_metrics": {
    "visual_confidence": 0-100,
    "metadata_confidence": 0-100,
    "combined_confidence": 0-100,
    "anatomy_score": 0-100,
    "text_score": 0-100,
    "texture_score": 0-100,
    "lighting_score": 0-100,
    "style_score": 0-100,
    "watermark_score": 0-100
  },
  "reconstructed_prompt": "The incredibly detailed, most probable technical AI prompt that generated this image, or N/A.",
  "detailed_reasoning": "A highly extensive, multi-paragraph expert dissertation on exactly what pixel-level evidence and stylistic cues drove this conclusion. Must be highly academic, methodical, and profoundly detailed."
}
"""

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class ImageForensicAnalysis(BaseModel):
    class VisualAnalysis(BaseModel):
        origin_verdict: str = "INCONCLUSIVE"
        confidence_score: int = Field(ge=0, le=100, default=50)
        suspected_generator: str = "unknown"
        detected_anomalies: List[str] = []
        style_markers: List[str] = []

    class MetadataFlags(BaseModel):
        has_camera_exif: bool = False
        software_tag: Optional[str] = None
        resolution: Optional[str] = None
        resolution_ratio_suspicious: bool = False
        ai_watermark_detected: bool = False
        ai_keywords_in_metadata: List[str] = []

    class ConfidenceMetrics(BaseModel):
        visual_confidence: int = Field(ge=0, le=100, default=50)
        metadata_confidence: int = Field(ge=0, le=100, default=50)
        combined_confidence: int = Field(ge=0, le=100, default=50)
        anatomy_score: int = Field(ge=0, le=100, default=0)
        text_score: int = Field(ge=0, le=100, default=0)
        texture_score: int = Field(ge=0, le=100, default=0)
        lighting_score: int = Field(ge=0, le=100, default=0)
        style_score: int = Field(ge=0, le=100, default=0)
        watermark_score: int = Field(ge=0, le=100, default=0)

    analysis: VisualAnalysis
    metadata: MetadataFlags
    confidence_metrics: ConfidenceMetrics
    reconstructed_prompt: str = "N/A"
    detailed_reasoning: str = ""


# ---------------------------------------------------------------------------
# Magic byte validators
# ---------------------------------------------------------------------------

MAGIC_BYTES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",  # WebP starts with RIFF....WEBP
}

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}

AI_METADATA_KEYWORDS = [
    "dream", "stability", "stable diffusion", "midjourney",
    "dall-e", "dalle", "openai", "imagen", "flux",
    "comfyui", "automatic1111", "invoke", "novelai",
    "synthid", "ai_generated", "c2pa",
]


def validate_image_magic(image_bytes: bytes) -> Optional[str]:
    """Validate image by checking magic bytes. Returns detected MIME type or None."""
    for magic, mime in MAGIC_BYTES.items():
        if image_bytes[:len(magic)] == magic:
            # Extra check for WebP — magic is RIFF but need WEBP at offset 8
            if mime == "image/webp" and image_bytes[8:12] != b"WEBP":
                continue
            return mime
    return None


# ---------------------------------------------------------------------------
# EXIF / metadata extraction (pure Python — no Pillow dependency)
# ---------------------------------------------------------------------------

def _extract_jpeg_exif(data: bytes) -> Dict[str, Any]:
    """Extract basic EXIF tags from JPEG without Pillow."""
    info: Dict[str, Any] = {}
    # Find APP1 marker (0xFFE1)
    idx = 2
    while idx < len(data) - 4:
        if data[idx] != 0xFF:
            break
        marker = data[idx + 1]
        length = struct.unpack(">H", data[idx + 2:idx + 4])[0]

        if marker == 0xE1:  # APP1 — EXIF
            segment = data[idx + 4:idx + 2 + length]
            segment_str = segment.decode("latin-1", errors="ignore").lower()
            # Check for common camera maker strings
            for maker in ["canon", "nikon", "sony", "fujifilm", "apple", "samsung", "google", "huawei", "xiaomi", "oppo"]:
                if maker in segment_str:
                    info["camera_maker"] = maker.title()
                    info["has_camera_exif"] = True
                    break
            # Check for software tags (AI tools often leave these)
            for kw in AI_METADATA_KEYWORDS:
                if kw in segment_str:
                    info.setdefault("ai_keywords", []).append(kw)
            # Look for software string
            sw_match = re.search(rb"software\x00.{0,2}(.{3,50}?)\x00", segment, re.IGNORECASE)
            if sw_match:
                info["software"] = sw_match.group(1).decode("latin-1", errors="ignore").strip()
            break

        idx += 2 + length

    return info


def _extract_png_metadata(data: bytes) -> Dict[str, Any]:
    """Extract tEXt/iTXt chunks from PNG for AI tool signatures."""
    info: Dict[str, Any] = {}
    idx = 8  # Skip PNG signature
    while idx < len(data) - 12:
        try:
            chunk_len = struct.unpack(">I", data[idx:idx + 4])[0]
            chunk_type = data[idx + 4:idx + 8].decode("ascii", errors="ignore")
        except (struct.error, UnicodeDecodeError):
            break

        if chunk_type in ("tEXt", "iTXt"):
            chunk_data = data[idx + 8:idx + 8 + min(chunk_len, 4096)]
            chunk_str = chunk_data.decode("latin-1", errors="ignore").lower()
            for kw in AI_METADATA_KEYWORDS:
                if kw in chunk_str:
                    info.setdefault("ai_keywords", []).append(kw)
            if "software" in chunk_str:
                parts = chunk_str.split("\x00")
                for i, p in enumerate(parts):
                    if p == "software" and i + 1 < len(parts):
                        info["software"] = parts[i + 1].strip()

        if chunk_type == "IEND":
            break

        idx += 12 + chunk_len  # 4 len + 4 type + data + 4 CRC

    return info


def extract_metadata(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """
    Extract metadata from image bytes.
    Returns a dict suitable for building MetadataFlags.
    """
    result: Dict[str, Any] = {
        "has_camera_exif": False,
        "software_tag": None,
        "resolution": None,
        "resolution_ratio_suspicious": False,
        "ai_watermark_detected": False,
        "ai_keywords_in_metadata": [],
        "file_size_bytes": len(image_bytes),
    }

    try:
        raw: Dict[str, Any] = {}
        if mime_type == "image/jpeg":
            raw = _extract_jpeg_exif(image_bytes)
        elif mime_type == "image/png":
            raw = _extract_png_metadata(image_bytes)
        # WebP metadata extraction is more complex; skip for v1

        result["has_camera_exif"] = raw.get("has_camera_exif", False)
        result["software_tag"] = raw.get("software")
        result["ai_keywords_in_metadata"] = raw.get("ai_keywords", [])

        if result["ai_keywords_in_metadata"]:
            result["ai_watermark_detected"] = True

        # Compute image dimensions for JPEG/PNG (basic extraction)
        dims = _get_dimensions(image_bytes, mime_type)
        if dims:
            w, h = dims
            result["resolution"] = f"{w}x{h}"
            # Many AI generators produce specific ratios (1:1, 16:9, 2:3)
            # Unusual high-res with no EXIF is suspicious
            if w * h > 2_000_000 and not result["has_camera_exif"]:
                result["resolution_ratio_suspicious"] = True

    except Exception as e:
        logger.warning(f"Metadata extraction failed (non-fatal): {e}")

    return result


def _get_dimensions(data: bytes, mime: str) -> Optional[Tuple[int, int]]:
    """Extract width/height from image bytes."""
    try:
        if mime == "image/png" and len(data) > 24:
            w = struct.unpack(">I", data[16:20])[0]
            h = struct.unpack(">I", data[20:24])[0]
            return (w, h)
        elif mime == "image/jpeg":
            idx = 2
            while idx < len(data) - 9:
                if data[idx] != 0xFF:
                    break
                marker = data[idx + 1]
                length = struct.unpack(">H", data[idx + 2:idx + 4])[0]
                if marker in (0xC0, 0xC2):  # SOF0 or SOF2
                    h = struct.unpack(">H", data[idx + 5:idx + 7])[0]
                    w = struct.unpack(">H", data[idx + 7:idx + 9])[0]
                    return (w, h)
                idx += 2 + length
    except (struct.error, IndexError):
        pass
    return None


# ---------------------------------------------------------------------------
# Main engine class
# ---------------------------------------------------------------------------

class ImageForensicEngine:
    """Analyzes images for AI-generation artifacts using Gemini Vision."""

    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def api_url(self) -> str:
        return f"{self._base_url}/{self.model}:generateContent?key={self.api_key}"

    async def analyze_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Run full forensic analysis on an image."""

        if not self.api_key:
            raise ValueError(
                "Gemini API Key not found. Set GEMINI_API_KEY in your .env file."
            )

        if len(image_bytes) > self.MAX_IMAGE_SIZE:
            raise ValueError(
                f"Image too large ({len(image_bytes) / 1024 / 1024:.1f}MB). "
                f"Maximum allowed is {self.MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB."
            )

        # Validate magic bytes
        detected_mime = validate_image_magic(image_bytes)
        if not detected_mime:
            raise ValueError(
                "Invalid image file. Only PNG, JPEG, and WebP are supported."
            )

        # Use detected MIME over claimed MIME for security
        mime_type = detected_mime

        try:
            # Step 1: Local metadata extraction
            metadata = extract_metadata(image_bytes, mime_type)
            logger.info(
                f"Image metadata: size={metadata['file_size_bytes']}B, "
                f"camera_exif={metadata['has_camera_exif']}, "
                f"ai_keywords={metadata['ai_keywords_in_metadata']}"
            )

            # Step 2: Encode image for Gemini
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Step 3: Build prompt with metadata context
            prompt_text = (
                f"{IMAGE_FORENSIC_PROMPT}\n\n"
                f"METADATA CONTEXT (pre-calculated):\n"
                f"{json.dumps(metadata, default=str)}\n\n"
                f"Analyze the attached image and return your forensic analysis in strict JSON."
            )

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {"inlineData": {"mimeType": mime_type, "data": b64_image}},
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.8,
                },
            }

            # Step 4: Call Gemini Vision
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(self.api_url, json=payload)

                # Fallback on 404 (model deprecation safety net)
                if response.status_code == 404 and "gemini" in self.model:
                    logger.warning(
                        f"Model {self.model} not found, "
                        f"falling back to gemini-flash-latest"
                    )
                    fallback_url = (
                        f"{self._base_url}/gemini-flash-latest"
                        f":generateContent?key={self.api_key}"
                    )
                    response = await client.post(fallback_url, json=payload)

                if response.status_code != 200:
                    error_body = response.text[:500]
                    logger.error(
                        f"Gemini Vision API returned {response.status_code}: "
                        f"{error_body}"
                    )
                    raise Exception(
                        f"Gemini API Error ({response.status_code}): {error_body}"
                    )

                data = response.json()
                content = (
                    data["candidates"][0]["content"]["parts"][0]["text"].strip()
                )

                # Cleanup JSON in case of markdown wrapping
                if content.startswith("```"):
                    content = re.sub(r"```[a-zA-Z]*\n?", "", content).strip()
                    content = content.rstrip("`").strip()

                result = json.loads(content)

            # Step 5: Enrich with local metadata
            result = self._enrich_with_metadata(result, metadata)

            # Step 6: Validate and return
            validated = ImageForensicAnalysis(**result)
            return validated.model_dump()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini Vision response as JSON: {e}")
            raise ValueError(f"Image forensic engine returned invalid JSON: {e}")
        except httpx.TimeoutException:
            logger.error("Gemini Vision API request timed out after 90s")
            raise TimeoutError(
                "Image forensic analysis timed out. Please try again."
            )
        except Exception as e:
            logger.error(f"IMAGE_FORENSIC_ERROR: {str(e)}", exc_info=True)
            raise

    def _enrich_with_metadata(
        self, result: Dict, metadata: Dict
    ) -> Dict[str, Any]:
        """Inject local metadata findings into the Gemini result."""

        # Ensure metadata section exists
        result.setdefault("metadata", {})
        result["metadata"]["has_camera_exif"] = metadata.get("has_camera_exif", False)
        result["metadata"]["software_tag"] = metadata.get("software_tag")
        result["metadata"]["resolution"] = metadata.get("resolution")
        result["metadata"]["resolution_ratio_suspicious"] = metadata.get(
            "resolution_ratio_suspicious", False
        )
        result["metadata"]["ai_watermark_detected"] = metadata.get(
            "ai_watermark_detected", False
        )
        result["metadata"]["ai_keywords_in_metadata"] = metadata.get(
            "ai_keywords_in_metadata", []
        )

        # Boost confidence if metadata has strong AI signals
        ai_kws = metadata.get("ai_keywords_in_metadata", [])
        if ai_kws:
            result.setdefault("confidence_metrics", {})
            result["confidence_metrics"]["metadata_confidence"] = min(
                100, 60 + len(ai_kws) * 15
            )
            # If AI keywords found and Gemini said INCONCLUSIVE, upgrade
            if result.get("analysis", {}).get("origin_verdict") == "INCONCLUSIVE":
                result["analysis"]["origin_verdict"] = "AI_GENERATED"

        # If camera EXIF present and Gemini said AI_GENERATED, reduce confidence
        if metadata.get("has_camera_exif") and result.get("analysis", {}).get(
            "origin_verdict"
        ) == "AI_GENERATED":
            result.setdefault("analysis", {})
            result["analysis"].setdefault("detected_anomalies", [])
            result["analysis"]["detected_anomalies"].append(
                "⚠ Camera EXIF data present — unusual for AI-generated images"
            )

        # Compute combined confidence
        cm = result.get("confidence_metrics", {})
        visual_conf = cm.get("visual_confidence", 50)
        meta_conf = cm.get("metadata_confidence", 50)
        cm["combined_confidence"] = round(visual_conf * 0.7 + meta_conf * 0.3)
        result["confidence_metrics"] = cm

        return result
