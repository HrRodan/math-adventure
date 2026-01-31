# Mathe-Abenteuer 🧮✨

**Ein interaktives Lernspiel für Erstleser (6-8 Jahre)**

Mathe-Abenteuer ist eine KI-gestützte Web-Anwendung, die endlose, personalisierte Geschichten generiert. Um in der Geschichte voranzukommen, müssen die Kinder kleine Mathe-Rätsel lösen (Klasse 2 Niveau).

## ✨ Features

*   **Unendliche Geschichten:** Wähle ein Thema (z.B. "Dinosaurier", "Weltraum"), und die KI schreibt ein individuelles Buch für dich.
*   **Intelligente Mathe-Rätsel:** Die KI integriert Aufgaben logisch in die Handlung ("Wir brauchen 15 Bretter, haben aber nur 8...").
*   **Multi-Model Support:** Nutze modernste KIs via OpenRouter, OpenAI oder Google Gemini.
*   **Fortschritt:** Sammle Sterne ⭐ für richtige Antworten. Alte Abenteuer werden gespeichert.
*   **Kindgerecht:** Große Schrift, Emojis, einfache Bedienung.

## 🏗 Projektstruktur

```
math-adventure/
├── backend/                # Server-Logik
│   ├── config.py           # Provider & Modell Konfiguration
│   ├── controller.py       # Spiel-Logik & State Management
│   ├── llm_engine.py       # LLM-Anbindung (LiteLLM)
│   ├── prompts.py          # Statische System-Prompts
│   └── database.py         # SQLAlchemy Modelle
├── frontend/               # Benutzeroberfläche
│   ├── ui.py               # Gradio Interface
│   └── assets/
│       └── styles.css      # CSS Styling
├── data/                   # Datenbank
│   └── adventure.db        # SQLite Datei
└── main.py                 # Start-Skript
```

## 🚀 Installation & Start

1.  **Voraussetzungen:** Python 3.12+ und `uv` (empfohlen).
2.  **Installation:**
    ```bash
    uv sync
    ```
3.  **Setup:** Erstelle eine `.env` Datei:
    ```ini
    GEMINI_API_KEY=dein_key
    OPENROUTER_API_KEY=dein_key
    # Optional:
    OPENAI_API_KEY=dein_key
    ```
4.  **Starten & Stoppen:**

    **Start (Hintergrund):**
    ```bash
    nohup uv run main.py > server.log 2>&1 &
    ```
    
    **Stoppen:**
    ```bash
    lsof -t -i:3000 | xargs -r kill -9
    ```

    Öffne `http://localhost:3000` im Browser.

## 🤖 Entwicklung

*   **Neue Modelle:** Füge sie einfach in `backend/config.py` hinzu.
*   **Prompts:** Änderungen an der "Persönlichkeit" in `backend/prompts.py`.
*   **Tests:** `uv run tests/test_coherence.py` prüft die Story-Logik.

## 📝 Lizenz
MIT License. Entwickelt für Bildungszwecke.