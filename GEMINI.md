# Project Context: Math Adventure

## 🎯 Core Concept
**Math Adventure** is an interactive storytelling game for children (ages 6-8). It combines generative AI with educational math problems. The key philosophy is **"Story First, Math Integrated"**.

## 🧠 Architectural Highlights

### 1. LLM Engine (`backend/llm_engine.py` & `backend/config.py`)
*   **Modular Providers:** The system abstracts LLM providers (Google, OpenAI, OpenRouter) via a central `config.py`.
*   **LiteLLM Integration:** We use `litellm` for standardized API calls.
*   **Strict Prefixes:**
    *   **OpenRouter:** Uses native `openrouter/` prefix (e.g., `openrouter/openai/gpt-oss-120b`).
    *   **Google:** Uses `gemini/` prefix.
*   **No Fallbacks:** If a specific model fails (e.g., API error), the request fails gracefully with a user message, rather than silently switching models. This ensures transparency.

### 2. Prompting Strategy (`backend/prompts.py`)
*   **Static System Prompt:** The system prompt is **constant** (no variables). This allows LLM providers to cache it efficiently, reducing latency and cost.
*   **Dynamic User Prompt:** All context (History, Theme, Math Examples) is injected into the *User Message*.
*   **Multi-Shot:** The user prompt contains diverse examples of math problems ("Situation -> Question") to guide the LLM without restricting it to a single type.
*   **JSON Enforcement:** All outputs are strictly validated via Pydantic (`StoryResponse`).

### 3. Frontend & Design (`frontend/`)
*   **Minimalism:** We rely on browser defaults for colors (Dark/Light mode support) but enforce the **'Lexend'** font for readability.
*   **Math Box:** The only heavily styled element is the math question container (`.math-box`), designed to be clean and distinct.
*   **UX:**
    *   **Delete Session:** Users can remove old stories.
    *   **Stars:** Persistent reward system stored in DB.
    *   **Retry:** Connection errors allow users to simply click "Check" again without losing progress.

## 🛠 Development Workflow

### Key Commands
*   **Run Server:** `nohup uv run main.py > server.log 2>&1 &`
*   **Stop Server:** `lsof -t -i:3000 | xargs -r kill -9`
*   **Test Coherence:** `uv run tests/test_coherence.py` (Simulates a game loop).

### Database
*   **SQLite:** `data/adventure.db`.
*   **Schema:** `sessions` (id, theme, model, stars) -> `messages` (role, content).
*   **State Recovery:** The controller rebuilds the full conversation history from the DB for every turn to ensure narrative consistency.

## 📝 Recent Decisions & Context
1.  **CSS Revert:** We moved back from a "playful/rotated" design to a clean, professional look to avoid visual clutter.
2.  **Model Config:** Models are defined in `PROVIDERS` dictionary in `config.py`. To add a model, edit this file.
3.  **Error Handling:** We use exponential backoff for retries (especially for "Model Overloaded" 503 errors).