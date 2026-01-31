# Mathe-Abenteuer 🧮✨

**Ein interaktives Lernspiel für Erstleser (6-8 Jahre)**

Mathe-Abenteuer ist eine KI-gestützte Web-Anwendung, die endlose, personalisierte Geschichten generiert. Um in der Geschichte voranzukommen, müssen die Kinder kleine Mathe-Rätsel lösen (Klasse 2 Niveau: bis 100, 10er Übergang).

## ✨ Features

*   **Unendliche Geschichten:** Wähle ein Thema (z.B. "Dinosaurier", "Weltraum"), und die KI schreibt ein individuelles Buch für dich.
*   **Intelligente Mathe-Rätsel:** Die KI integriert Aufgaben logisch in die Handlung. Die Aufgaben passen sich der Situation an (Kettenaufgaben, Lückentexte, Sachaufgaben).
*   **Multi-Model Support:** Nutze modernste KIs via OpenRouter, OpenAI oder Google Gemini.
*   **Hinter die Kulissen:** Ein ausklappbarer Bereich ("Story-Plan") zeigt, was die KI intern plant (den roten Faden).
*   **Kindgerecht:** Große Schrift, minimalistisches Design, einfache Bedienung.

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

## 🧠 Prompt Engineering & Architektur

Das Herzstück der Anwendung ist eine zweistufige Prompt-Strategie, die **Performance** (Caching) mit **Kreativität** verbindet:

### 1. Der System-Prompt (Statisch)
Der System-Prompt (`backend/prompts.py`) ist konstant und ändert sich nie.
*   **Vorteil:** Moderne LLMs können diesen riesigen Textblock **cachen**, was Anfragen extrem beschleunigt.
*   **Inhalt:** Persona, Mathe-Regeln (0-100), und Multi-Shot Beispiele.

### 2. Der User-Prompt (Dynamisch)
Dieser Teil wird bei jedem Zug neu generiert (`backend/llm_engine.py`).
*   **Start:** Die KI wird aufgefordert, einen internen `story_arc` (Handlungsplan) zu entwerfen und Kapitel 1 zu schreiben.
*   **Fortsetzung:** Der `story_arc` wird als "Regieanweisung" mitgegeben, damit die KI den roten Faden nicht verliert. Die KI entscheidet selbst, welcher Aufgabentyp zur aktuellen Handlung passt.

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

## 📝 Lizenz
MIT License. Entwickelt für Bildungszwecke.
