# Project Context: Math Adventure

## 🎯 Core Concept
**Math Adventure** is an interactive storytelling game for children (ages 6-8). It combines generative AI with educational math problems. The key philosophy is **"Story First, Math Integrated"**.

## 🧠 Architectural Highlights

### 1. LLM Engine (`backend/llm_engine.py` & `backend/config.py`)
*   **Modular Providers:** The system abstracts LLM providers (Google, OpenAI, OpenRouter) via a central `config.py`.
*   **LiteLLM Integration:** We use `litellm` for standardized API calls.
*   **Strict Prefixes:**
    *   **OpenRouter:** Uses native `openrouter/` prefix.
    *   **Google:** Uses `gemini/` prefix.
*   **Robustness:** No automated fallbacks between models (fail-fast to show config errors). Exponential backoff for API retries.

### 2. Prompting Strategy (`backend/prompts.py`)
*   **Static System Prompt:** The system prompt is **constant** (no variables). This allows LLM providers to cache it efficiently (Context Caching), reducing latency and cost.
*   **Dynamic User Prompt:**
    *   **Start:** Requests a `story_arc` (hidden plan) and Chapter 1.
    *   **Continuation:** Injects the `story_arc` into the prompt to maintain long-term coherence.
*   **Multi-Shot:** The system prompt contains diverse examples of math problems ("Situation -> Question") to guide the LLM without restricting it to a single type.
*   **JSON Enforcement:** All outputs are strictly validated via Pydantic (`StoryResponse`, `InitialStoryResponse`).

### 3. Frontend & Design (`frontend/`)
*   **Minimalism:** Browser defaults for colors (Dark/Light mode support).
*   **Math Box:** The only heavily styled element is the math question container (`.math-box`), designed to be clean and distinct.
*   **Arc Reveal:** An accordion allows users to see the internal `story_arc`.

## 🛠 Development Workflow

### Key Commands
*   **Run Server:** `nohup uv run main.py > server.log 2>&1 &`
*   **Stop Server:** `lsof -t -i:3000 | xargs -r kill -9`
*   **Test Coherence:** `uv run tests/test_coherence.py` (Simulates a game loop).

### Database
*   **SQLite:** `data/adventure.db`.
*   **Schema:** `sessions` (theme, model, story_arc) -> `messages` (role, content).
*   **State Recovery:** The controller rebuilds the full conversation history from the DB for every turn.

## 📝 Maintenance Guidelines

### Documentation Standards
*   **Docstrings:** Every class and public method MUST have a docstring explaining *what* it does, *args*, and *return values*.
*   **Type Hints:** Use standard Python typing (`List`, `Dict`, `Optional`) for all function signatures.
*   **Comments:** Use comments sparingly but effectively for complex logic blocks (e.g., prompt assembly, retry loops).

### Adding Features
1.  **Config:** Update `backend/config.py` for new models.
2.  **Schema:** Update Pydantic models in `llm_engine.py` if output structure changes.
3.  **UI:** Update `frontend/ui.py` only if necessary. Keep CSS minimal.
