# The Forensic Engine (PREE)

**The Prompt Reverse Engineering Engine (PREE)** is an advanced, high-fidelity AI forensic analyzer. Designed with the precision of a cyber-intelligence platform, it specializes in detecting AI-generated text and imagery and meticulously reverse-engineering the exact prompts, system instructions, and technical parameters used to create them.

---

## 🎯 Core Capabilities

The Forensic Engine operates by deeply analyzing structural, lexical, visual, and mathematical anomalies.

### 📝 Text Forensics
- **Lexical Fingerprinting:** Detects LLM-specific word biases (e.g., "delve", "tapestry", "seamless") and vocabulary densities to perform accurate model attribution (GPT-4, Claude 3.5, Gemini 1.5).
- **Structural Mapping:** Identifies hidden formatting instructions, implicit structural constraints, and cadence monotony.
- **Parameter Estimation:** Accurately estimates top-P, temperature, and creativity settings based on rhythmic sentence variance.
- **Prompt Reconstruction:** Synthesizes the exact text constraints and persona definitions used in the original master prompt.

### 👁️ Visual Forensics
- **Pixel & Anatomy Anomalies:** Detects microscopic generative errors like non-euclidean limbs, uneven irises, and impossible skin topologies.
- **Lighting & Texture Algorithms:** Identifies physically implausible Volumetric shadows, Voronoi noise patterns, or flat global illumination.
- **Metadata Scrubbing:** Extracts hidden software tags, unusual resolution ratios, and EXIF footprints common in AI pipelines.
- **Generator Attribution:** Classifies the visual aesthetic to specifically identify Image Generators (Midjourney v6, DALL·E 3, SDXL, Flux).

---


## 🏗️ Architecture Stack

- **Backend (API):** Python, FastAPI, Pydantic, httpx
- **Frontend (Web):** Next.js 14, React, TypeScript
- **Styling:** Vanilla CSS, Framer Motion (Micro-animations)
- **Data Visualization:** Recharts (Forensic Radar graphs)
- **AI Integration:** Google Gemini API / Vision Models

---

## 🚀 Local Deployment Guide

### Prerequisites
- Node.js v18+
- Python 3.10+
- A Google Gemini API Key

### 1. Setup the Backend API
```bash
# Navigate to API directory
cd api

# Install Python requirements
pip install -r requirements.txt

# Create an env file from the example
cp .env.example .env

# Open .env and add your GEMINI_API_KEY
# GEMINI_API_KEY="AIzaSyYourKeyHere..."

# Start the FastApi Server
python main.py
# Server will run on http://0.0.0.0:8000
```

### 2. Setup the Frontend Dashboard
```bash
# Open a new terminal and navigate to the web directory
cd web

# Install Node dependencies
npm install

# Optional: Add .env.local to point to custom API URL (defaults to localhost:8000)
# echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the development server
npm run dev
# Dashboard will be available at http://localhost:3000
```

---

## 📋 Environment Variables Reference
**Backend `api/.env`**
- `GEMINI_API_KEY` (Required): Your Gemini Developer Key.
- `GEMINI_MODEL` (Optional): Target model (defaults to `gemini-1.5-pro` / `gemini-1.5-flash`).
- `PORT` (Optional): Server port (defaults to `8000`).
- `CORS_ORIGINS` (Optional): Permitted frontend connections (defaults to `http://localhost:3000`).

**Frontend `web/.env.local`**
- `NEXT_PUBLIC_API_URL` (Required in Prod): Location of the FastAPI backend.


