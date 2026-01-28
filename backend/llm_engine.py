import os
import json
import random
import re
from litellm import completion
from dotenv import load_dotenv
from backend.prompts import get_system_prompt, get_fallback_scenario

# Umgebungsvariablen laden
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class LLMEngine:
    """
    Zentrale Klasse für die Interaktion mit verschiedenen LLM-Providern.
    Abstrahiert die API-Aufrufe und bereinigt die Antworten.
    """
    
    def __init__(self):
        self.api_key_google = os.getenv("GEMINI_API_KEY")
        self.api_key_openrouter = os.getenv("OPENROUTER_API_KEY")
        
    def _clean_json(self, text):
        """
        Versucht, ein valides JSON-Objekt aus dem Antworttext zu extrahieren.
        Entfernt Markdown-Codeblöcke und repariert einfache Formatfehler.
        """
        try:
            return json.loads(text)
        except:
            # Fallback: Suche nach JSON-Muster mit Regex
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return None

    def generate_turn(self, history, model="gemini/gemini-2.0-flash", theme="Abenteuer"):
        """
        Generiert das nächste Kapitel der Geschichte basierend auf dem bisherigen Verlauf.
        
        Args:
            history (list): Liste der bisherigen Nachrichten (Context Window).
            model (str): ID des zu verwendenden Modells.
            theme (str): Das Thema der Geschichte.
            
        Returns:
            dict: JSON-Objekt mit 'story', 'question' und 'answer'.
        """
        
        # Zufallsauswahl des Aufgabentyps für Abwechslung
        task_type = random.choice([
            "STANDARD (z.B. '7 + 8 = ?')",
            "GAP (z.B. '15 - ? = 9')",
            "CHAIN (3 Zahlen, z.B. '5 + 4 - 2 = ?')",
            "TEXT (z.B. 'Das Doppelte von 6?')"
        ])
        
        # System-Prompt laden (ausgelagert für bessere Wartbarkeit)
        system_instructions = get_system_prompt(theme, task_type)
        
        # Nachrichtenhistorie aufbauen
        messages = [{"role": "system", "content": system_instructions}] + history
        
        try:
            # Modell-Mapping (Alias -> Echter Modellname für LiteLLM)
            lite_model = model
            if "gemini" in model and not model.startswith("gemini/"):
                lite_model = f"gemini/{model}"
            elif "gpt" in model and not model.startswith("openai/"):
                lite_model = f"openai/{model}"

            # Passenden API-Key wählen
            api_key = self.api_key_google if "gemini" in lite_model else self.api_key_openrouter
            api_base = "https://openrouter.ai/api/v1" if "openrouter" in lite_model or "gpt-oss" in lite_model else None
            
            # API-Aufruf (Sync)
            response = completion(
                model=lite_model,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                temperature=0.85, # Kreativität für Storytelling
                max_tokens=600,
                response_format={"type": "json_object"} 
            )
            
            content = response.choices[0].message.content
            parsed = self._clean_json(content)
            
            # Validierung: Sind alle notwendigen Felder da?
            if not parsed or 'story' not in parsed or 'answer' not in parsed:
                print(f"Warnung: Ungültiges JSON erhalten: {content}")
                return get_fallback_scenario()
                
            return parsed

        except Exception as e:
            print(f"LLM Fehler: {e}")
            import traceback
            traceback.print_exc()
            return get_fallback_scenario()
