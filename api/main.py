from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from engine import ForensicEngine, ForensicAnalysis
from image_engine import ImageForensicEngine, validate_image_magic, ALLOWED_MIME_TYPES
from fastapi.responses import JSONResponse
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("forensic-api")

app = FastAPI(
    title="The Forensic Engine API",
    description="AI-generated text forensic analyzer — reverse-engineers prompts and system parameters.",
    version="1.1.0",
)

# CORS — configurable via environment
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="The text to analyze forensically.")


# Initialize the engine (reads GEMINI_API_KEY from .env)
engine = ForensicEngine()
image_engine = ImageForensicEngine()


@app.get("/")
async def root():
    return {
        "service": "The Forensic Engine",
        "version": "1.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "engine_ready": engine.api_key is not None,
    }


@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    """Run a full forensic analysis on the provided text."""
    try:
        logger.info(f"Analyzing text — length: {len(request.text)} chars")
        result = await engine.analyze(request.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        logger.error(f"FORENSIC_ENGINE_CRASH: {error_msg}", exc_info=True)
        
        # Friendly error for quota issues
        if "429" in error_msg or "quota" in error_msg.lower():
            friendly_detail = "AI Quota Exceeded. The Gemini API key has reached its limit. Please try again later or use a different API key."
        else:
            friendly_detail = f"Forensic analysis failed: {error_msg}"
            
        raise HTTPException(
            status_code=500,
            detail=friendly_detail,
        )


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/analyze/image")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """Run a full forensic analysis on an uploaded image."""
    try:
        # Validate MIME type from header
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type: {file.content_type}. "
                       f"Accepted: PNG, JPEG, WebP.",
            )

        # Read and validate size
        image_bytes = await file.read()
        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"Image too large ({len(image_bytes) / 1024 / 1024:.1f}MB). "
                       f"Maximum is 10MB.",
            )

        # Validate magic bytes (don't trust Content-Type alone)
        detected_mime = validate_image_magic(image_bytes)
        if not detected_mime:
            raise HTTPException(
                status_code=422,
                detail="Invalid image file. The file does not appear to be "
                       "a valid PNG, JPEG, or WebP image.",
            )

        logger.info(
            f"Analyzing image — size: {len(image_bytes)} bytes, "
            f"type: {detected_mime}, name: {file.filename}"
        )

        result = await image_engine.analyze_image(image_bytes, detected_mime)
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        logger.error(f"IMAGE_FORENSIC_CRASH: {error_msg}", exc_info=True)

        if "429" in error_msg or "quota" in error_msg.lower():
            friendly_detail = (
                "AI Quota Exceeded. The Gemini API key has reached its limit. "
                "Please try again later or use a different API key."
            )
        else:
            friendly_detail = f"Image forensic analysis failed: {error_msg}"

        raise HTTPException(status_code=500, detail=friendly_detail)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
