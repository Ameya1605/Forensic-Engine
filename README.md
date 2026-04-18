# The Forensic Engine (PREE)

An advanced AI forensic analyzer designed to reverse-engineer AI-generated text, reconstruct original prompts, and estimate system parameters.

## Core Features
- **Lexical Fingerprinting**: Detects common LLM tropes.
- **Structural Mapping**: Identifies requested formatting constraints.
- **Parameter Estimation**: Reconstructs probable temperature and personas.
- **Prompt Reconstruction**: Outputs the optimized prompt that likely generated the input.

## Project Structure
- `/api`: FastAPI backend for forensic analysis.
- `/web`: Next.js frontend dashboard.

## Tech Stack
- **Backend**: Python, FastAPI, Pydantic.
- **Frontend**: Next.js, TypeScript, Vanilla CSS.
- **Design**: Premium Dark Mode, Glassmorphism, Recharts.
