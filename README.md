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
...
```

## 🧠 Prompt Engineering & Architektur

Das Herzstück der Anwendung ist eine zweistufige Prompt-Strategie, die **Performance** (Caching) mit **Kreativität** verbindet:

### 1. Der System-Prompt (Statisch)
Der System-Prompt (`backend/prompts.py`) ist konstant und ändert sich nie.
*   **Vorteil:** Moderne LLMs (wie Gemini 1.5/2.0) können diesen riesigen Textblock **cachen**, was Anfragen extrem beschleunigt und Kosten spart.
*   **Inhalt:**
    *   **Persona:** "Bestseller-Kinderbuchautor".
    *   **Regeln:** Sprache (Deutsch), Stil (Emojis), JSON-Format.
    *   **Mathe-Beispiele (Multi-Shot):** Eine Liste verschiedener Aufgabentypen (Subtraktion, Lücken, Kettenaufgaben mit 3 Zahlen), an denen sich das Modell orientiert.

### 2. Der User-Prompt (Dynamisch)
Dieser Teil wird bei jedem Zug neu generiert (`backend/llm_engine.py`).
*   **Inhalt:**
    *   **Thema:** Das vom Kind gewählte Szenario (z.B. "Ritterburg").
    *   **Historie:** Eine Zusammenfassung der bisherigen Geschichte ("Was bisher geschah").
    *   **Anweisung:** "Erzähle weiter und integriere ein passendes Mathe-Rätsel."
*   **Freiheit:** Wir zwingen das Modell nicht in starre Schablonen ("Mache jetzt eine Plus-Aufgabe"), sondern lassen es anhand der *Handlung* entscheiden, welcher der gelernten Aufgabentypen am besten passt.

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