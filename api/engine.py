import json
import os
import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache
import httpx
from pydantic import BaseModel, Field
from tropes import AI_HALLMARKS

logger = logging.getLogger(__name__)

# The Master System Prompt for PREE
MASTER_SYSTEM_PROMPT = """
ROLE:
You are the Prompt Reverse Engineering Engine (PREE), an elite, highly advanced AI forensic analyzer operating at the highest level of academic and technical rigor. Your primary objective is to forensically breakdown AI-generated text outputs, performing a meticulous, deep-dive analysis to reverse-engineer the exact prompt, constraints, and system parameters with unparalleled accuracy and extreme detail.

OBJECTIVE:
Given an isolated piece of AI-generated text AND a set of pre-calculated forensic markers, execute an exhaustive, multi-step forensic breakdown. Your analysis must be highly accurate, citing specific evidence from the text to justify your parameter and model estimations. You will not engage in conversation. Output MUST be a strict JSON object containing your deep-dive forensic analysis.

FORENSIC METHODOLOGY (Be extremely detailed):
1. Lexical Fingerprinting Analysis: Deeply analyze "detected_tropes", syntactic structures, and vocabulary anomalies to identify model-specific biases.
2. Structural Mapping: Extract deeply hidden formatting constraints, instructional cadences, and implicit framework requests made by the user.
3. Audience & Tone Inference: Provide a high-resolution profile of the target persona, psychological framing, and intended audience level.
4. Parameter Estimation: Precisely estimate temperature, Top-P, and Top-K based on lexical variance, creativity, and stochastic markers.
5. Model Attribution: Provide a high-confidence estimation of the originating model (e.g., GPT-4, Claude 3 Opus, Gemini 1.5 Pro) with strict evidence.
6. Prompt Reconstruction: Synthesize the most probable, highly optimized user prompt, including system instructions, roleplay constraints, and format commands.

OUTPUT FORMAT:
You must output ONLY a valid JSON object. Do not include markdown formatting.
Structure:
{
  "analysis": {
    "primary_intent": "String (Detailed intent)",
    "target_audience": "String (Highly specific audience profile)",
    "tone_and_style": "String (Granular stylistic breakdown)",
    "temperature_estimate": "Float (0.0 to 1.0)",
    "detected_constraints": ["Array of Strings (Exhaustive list of structural rules)"],
    "ai_fingerprints": ["Array of Strings (Specific textual evidence)"],
    "suspected_model": "String (Specific model version if possible, e.g., GPT-4o, Claude 3.5 Sonnet)"
  },
  "confidence_metrics": {
    "intent_confidence": "Integer (0-100)",
    "formatting_signal_strength": "Integer (0-100)",
    "lexical_match_score": "Integer (0-100)"
  },
  "reconstructed_prompt": "String (The fully reconstructed, highly detailed master prompt)",
  "detailed_reasoning": "String (A comprehensive, multi-paragraph expert forensic breakdown explaining EXACTLY how you arrived at your conclusions, citing specific words and structural evidence from the text.)"
}
"""


class ForensicAnalysis(BaseModel):
    class DetailedAnalysis(BaseModel):
        primary_intent: str
        target_audience: str
        tone_and_style: str
        temperature_estimate: float = Field(ge=0.0, le=1.0)
        detected_constraints: List[str]
        ai_fingerprints: List[str]
        suspected_model: str = "unknown"

    class ConfidenceMetrics(BaseModel):
        intent_confidence: int = Field(ge=0, le=100)
        formatting_signal_strength: int = Field(ge=0, le=100)
        lexical_match_score: int = Field(ge=0, le=100)

    analysis: DetailedAnalysis
    confidence_metrics: ConfidenceMetrics
    reconstructed_prompt: str
    detailed_reasoning: str = "Analysis completed."


# Module-level cache to avoid lru_cache-on-method memory leak
@lru_cache(maxsize=256)
def _calculate_statistics(text: str) -> Dict[str, Any]:
    """Performs statistical analysis on text for forensic scoring."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = re.findall(r'\w+', text.lower())
    word_count = len(words)

    if not sentences or word_count == 0:
        return {
            "sentence_variance": 0,
            "avg_sentence_length": 0,
            "lexical_density": 0,
            "detected_tropes": [],
            "structural_patterns": [],
            "model_bias_scores": {},
            "trope_count": 0,
        }

    # Sentence length variance (rhythmic analysis)
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_len = sum(sentence_lengths) / len(sentence_lengths)
    variance = sum((l - avg_len) ** 2 for l in sentence_lengths) / len(sentence_lengths)

    # Lexical density (unique words / total words)
    unique_words = set(words)
    lexical_density = round(len(unique_words) / word_count, 3) if word_count > 0 else 0

    # Trope detection (Lexical Fingerprinting)
    tropes_list = AI_HALLMARKS.get("lexical_fingerprints", [])
    detected_tropes = [trope for trope in tropes_list if trope.lower() in text.lower()]

    # Structural pattern detection
    structural_list = AI_HALLMARKS.get("structural_patterns", [])
    structural_hits = []
    text_lower = text.lower()
    if re.search(r'\d+\.\s', text):
        structural_hits.append("Step-by-step numbering")
    if text.count('**') >= 4:
        structural_hits.append("Excessive use of bolding for emphasis")
    if text.count('- ') >= 5 or text.count('• ') >= 3:
        structural_hits.append("Bullet-point heavy formatting")
    if variance < 8.0 and len(sentences) > 3:
        structural_hits.append("Balanced sentence lengths (rhythmic monotony)")

    # Model attribution scoring
    model_bias = AI_HALLMARKS.get("model_specific_bias", {})
    model_scores = {}
    for model, markers in model_bias.items():
        score = sum(1 for m in markers if m.lower() in text_lower)
        if score > 0:
            model_scores[model] = round(score / len(markers) * 100, 1)

    return {
        "sentence_variance": round(variance, 2),
        "avg_sentence_length": round(avg_len, 2),
        "lexical_density": lexical_density,
        "detected_tropes": detected_tropes,
        "structural_patterns": structural_hits,
        "model_bias_scores": model_scores,
        "trope_count": len(detected_tropes),
        "word_count": word_count,
        "sentence_count": len(sentences),
    }


class ForensicEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-pro-latest")
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def api_url(self) -> str:
        """Build API URL without exposing key in logs."""
        return f"{self._base_url}/{self.model}:generateContent?key={self.api_key}"

    async def analyze(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "Gemini API Key not found. Set GEMINI_API_KEY in your .env file."
            )

        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        try:
            # Pre-processing & Statistical Analysis
            stats = _calculate_statistics(text)
            logger.info(
                f"Stats: {stats['trope_count']} tropes, "
                f"variance={stats['sentence_variance']}, "
                f"words={stats.get('word_count', 'N/A')}"
            )

            prompt = (
                f"{MASTER_SYSTEM_PROMPT}\n\n"
                f"STATISTICAL CONTEXT:\n{json.dumps(stats, default=str)}\n\n"
                f"INPUT TEXT:\n{text}\n\n"
                f"Return analysis in strict JSON."
            )

            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "topP": 0.8,
                    },
                }

                response = await client.post(self.api_url, json=payload)

                if response.status_code == 404 and "gemini" in self.model:
                    logger.warning(f"Model {self.model} not found, falling back to gemini-flash-latest")
                    fallback_url = f"{self._base_url}/gemini-flash-latest:generateContent?key={self.api_key}"
                    response = await client.post(fallback_url, json=payload)
                
                if response.status_code != 200:
                    error_body = response.text[:500]
                    logger.error(f"Gemini API returned {response.status_code}: {error_body}")
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

                # Enrich with pre-calculated statistics
                result = self._enrich_result(result, stats)

                validated_result = ForensicAnalysis(**result)
                return validated_result.model_dump()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"Forensic engine returned invalid JSON: {e}")
        except httpx.TimeoutException:
            logger.error("Gemini API request timed out after 60s")
            raise TimeoutError("Forensic analysis timed out. Please try again.")
        except Exception as e:
            logger.error(f"FORENSIC_ENGINE_ERROR: {str(e)}", exc_info=True)
            raise

    def _enrich_result(self, result: Dict, stats: Dict) -> Dict:
        """Post-process and enrich the LLM result with local analysis."""

        # Human origin detection
        is_likely_human = (
            stats["trope_count"] == 0
            and stats["sentence_variance"] > 30.0
            and stats.get("lexical_density", 0) > 0.6
        )
        if is_likely_human:
            result.setdefault("analysis", {})
            result["analysis"].setdefault("ai_fingerprints", [])
            result["analysis"]["ai_fingerprints"].insert(
                0, "⚠ LIKELY HUMAN ORIGIN (High Variance, Zero Tropes)"
            )

        # Inject lexical match score if LLM didn't provide it
        if "lexical_match_score" not in result.get("confidence_metrics", {}):
            lexical_score = min(100, stats["trope_count"] * 12)
            result.setdefault("confidence_metrics", {})[
                "lexical_match_score"
            ] = lexical_score

        # Inject model attribution from local analysis
        model_scores = stats.get("model_bias_scores", {})
        if model_scores:
            top_model = max(model_scores, key=model_scores.get)
            result.setdefault("analysis", {}).setdefault(
                "suspected_model", top_model
            )

        # Inject structural pattern info
        if stats.get("structural_patterns"):
            result.setdefault("analysis", {}).setdefault(
                "detected_constraints", []
            )
            for pattern in stats["structural_patterns"]:
                if pattern not in result["analysis"]["detected_constraints"]:
                    result["analysis"]["detected_constraints"].append(pattern)

        return result
