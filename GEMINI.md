# Project Context: Math Adventure

## Project Overview
**Math Adventure** is an AI-powered interactive storytelling game designed for children (approx. ages 6-8). It dynamically generates infinite adventure stories where the narrative progress is gated by age-appropriate math problems (Addition/Subtraction 0-20, simple multiplication, sequences).

The application is built as a **Single Page Application (SPA)** using **Gradio** for the frontend, served by a **Python** backend that orchestrates **LLM** calls (via LiteLLM) and manages state in a **SQLite** database.

## Architecture

### 1. Backend (`backend/`)
*   **`llm_engine.py`**: Handles interaction with Large Language Models (Gemini 2.0/3.0, GPT-OSS). Uses `litellm` for provider abstraction and robust error handling (JSON repair).
*   **`controller.py`**: The game loop controller. It receives user input, validates math answers locally (deterministic), and triggers the LLM for the next story chapter.
*   **`database.py`**: Uses **SQLAlchemy** to manage the SQLite database (`data/adventure.db`). Stores game sessions, full chat history, and collected stars (rewards).
*   **`prompts.py`**: Central repository for system prompts. Defines the "Dungeon Master" persona and the strict rules for generating math tasks without revealing answers.

### 2. Frontend (`frontend/`)
*   **`ui.py`**: Defines the user interface using **Gradio**. It handles session selection, chat display, and input forms.
*   **`assets/styles.css`**: Custom CSS to ensure a child-friendly, accessible design (large fonts, 'Lexend' typeface, high contrast, "Light Mode only").

### 3. Data (`data/`)
*   **`adventure.db`**: SQLite database file. Created automatically on startup if missing.

## Key Technologies
*   **Language:** Python 3.12+
*   **Dependency Management:** `uv`
*   **UI Framework:** Gradio (>= 6.5.0)
*   **AI Interface:** LiteLLM
*   **Database:** SQLAlchemy (SQLite)

## Build & Run Instructions

**Prerequisites:**
*   `uv` installed.
*   `.env` file in `/` with `GEMINI_API_KEY` and/or `OPENROUTER_API_KEY`.

**Setup:**
```bash
cd math-adventure
uv sync
```

**Run Server:**
```bash
uv run main.py
```
The application will be available at `http://localhost:3000`.

**Run Tests:**
To verify the story generation logic autonomously:
```bash
uv run tests/test_coherence.py
```

## Development Conventions
*   **Modular Design:** Keep logic (Backend), presentation (Frontend/CSS), and data (DB) separate.
*   **Prompt Engineering:** Modify `backend/prompts.py` to change the AI's behavior or math difficulty level. Do not hardcode prompts in `llm_engine.py`.
*   **Styling:** Use `frontend/assets/styles.css` for all visual changes. Avoid inline CSS in Python where possible.
*   **State Management:** The backend is stateless regarding the immediate turn logic; the frontend passes the required state (Session ID) to the controller, which rehydrates context from the DB.
