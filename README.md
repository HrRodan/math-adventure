# Mathe-Abenteuer 🧮✨

**Ein interaktives Lernspiel für Erstleser (6-8 Jahre)**

Mathe-Abenteuer ist eine KI-gestützte Web-Anwendung, die endlose, personalisierte Geschichten generiert. Um in der Geschichte voranzukommen, müssen die Kinder kleine Mathe-Rätsel lösen (Klasse 1-2 Niveau).

## ✨ Features

*   **Unendliche Geschichten:** Wähle ein Thema (z.B. "Dinosaurier", "Weltraum"), und die KI schreibt ein individuelles Buch für dich.
*   **Lernspaß:** Die Matheaufgaben (Plus, Minus, Lückenaufgaben bis 20, einfaches 1x1) sind logisch in die Handlung integriert.
*   **Kindgerechtes Design:** Große Schrift ('Lexend'), bunte Farben und klare Strukturen. Optimiert für Tablets und Desktop.
*   **Gedächtnis:** Das Spiel speichert den Fortschritt automatisch. Alte Abenteuer können jederzeit fortgesetzt werden.
*   **Technik:** Nutzt modernste LLMs (Gemini, GPT-4) für kohärente Erzählungen.

## 🏗 Projektstruktur

Das Projekt ist modular aufgebaut, um Wartbarkeit und Erweiterbarkeit zu gewährleisten:

```
math-adventure/
├── backend/                # Server-Logik
│   ├── controller.py       # Spiel-Logik & State Management
│   ├── database.py         # SQLAlchemy Modelle & SQLite Zugriff
│   ├── llm_engine.py       # LLM-Anbindung (LiteLLM)
│   └── prompts.py          # Zentraler Speicher für System-Prompts
├── frontend/               # Benutzeroberfläche
│   ├── ui.py               # Gradio Interface Definition
│   └── assets/
│       └── styles.css      # CSS Styling (Design)
├── data/                   # Datenbank-Speicherort
│   └── adventure.db        # SQLite Datei
├── tests/                  # Automatisierte Tests
│   └── test_coherence.py   # Simuliert 20 Spielrunden
├── main.py                 # Start-Skript
├── .env                    # API-Schlüssel (nicht im Repo!)
└── README.md               # Dokumentation
```

## 🚀 Installation & Start

1.  **Voraussetzungen:** Python 3.12+ und `uv` (oder pip).
2.  **Installation:**
    ```bash
    uv pip install litellm gradio sqlalchemy python-dotenv
    ```
3.  **Setup:** Erstelle eine `.env` Datei im Hauptverzeichnis:
    ```ini
    GEMINI_API_KEY=dein_key
    OPENROUTER_API_KEY=dein_key
    ```
### 4. Starten & Stoppen

**Standard (Vordergrund):**
Ideal zum Testen, da Fehlermeldungen direkt in der Konsole erscheinen.
```bash
uv run main.py
```
*Zum Stoppen einfach `Strg + C` drücken.*

**Hintergrund (Produktiv):**
Der Server läuft weiter, auch wenn du das Terminal schließt.
```bash
nohup uv run main.py > server.log 2>&1 &
```

**Server stoppen (Hintergrund):**
Falls der Port 3000 belegt ist oder du den Hintergrund-Prozess beenden willst:
```bash
lsof -t -i:3000 | xargs -r kill -9
```

## 📖 Abenteuer fortsetzen

## 🤖 Entwicklungshinweise

*   **Prompts:** Änderungen an der KI-Persönlichkeit bitte nur in `backend/prompts.py` vornehmen.
*   **Design:** Anpassungen am Aussehen gehören in `frontend/assets/styles.css`.
*   **Tests:** Vor jedem größeren Commit bitte `python tests/test_coherence.py` ausführen, um sicherzustellen, dass die Story-Generierung noch funktioniert.

## 📝 Lizenz
MIT License. Entwickelt für Bildungszwecke.
