import os
import json
import random
import re
from litellm import completion
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from backend.prompts import get_system_prompt, get_fallback_scenario

# Umgebungsvariablen laden
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Definition des erwarteten Schemas
class StoryResponse(BaseModel):
    story: str = Field(..., description="Der Text des nächsten Kapitels der Geschichte (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe, die das Kind lösen muss.")
    answer: int = Field(..., description="Die numerische Lösung der Aufgabe (Ganzzahl).")

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
            data = json.loads(text)
            # Falls LLM eine Liste zurückgibt (z.B. [{}])
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except:
            # Fallback: Suche nach JSON-Muster mit Regex
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    return data
                except:
                    pass
            return None

    def generate_turn(self, history, model="gemini/gemini-3-flash-preview", theme="Abenteuer"):
        """
        Generiert das nächste Kapitel der Geschichte basierend auf dem bisherigen Verlauf.
        """
        
        # Erweiterte Aufgabentypen für mehr Abwechslung
        task_options = [
            "STANDARD (z.B. '7 + 8 = ?')",
            "GAP (z.B. '15 - ? = 9')",
            "CHAIN (3 Zahlen, z.B. '5 + 4 - 2 = ?')",
            "TEXT (z.B. 'Das Doppelte von 6?')",
            "SEQUENCE (z.B. '2, 4, 6, ?' - Nächste Zahl)",
            "MONEY (z.B. '3 Euro + 4 Euro')",
            "ZERO (Rechnen mit Null, z.B. '5 + 0')"
        ]
        task_type = random.choice(task_options) 
        
        # System-Prompt laden
        system_instructions = get_system_prompt(theme, task_type)
        
        messages = [{"role": "system", "content": system_instructions}] + history
        
        try:
            # Modell-Mapping
            lite_model = model
            if "gemini" in model and not model.startswith("gemini/"):
                lite_model = f"gemini/{model}"
            elif "gpt" in model and not model.startswith("openai/"):
                lite_model = f"openai/{model}"

            # API-Key Wahl
            api_key = None
            api_base = None
            
            if "gemini" in lite_model:
                api_key = self.api_key_google
            elif "openrouter" in lite_model or "gpt-oss" in lite_model:
                api_key = self.api_key_openrouter
                api_base = "https://openrouter.ai/api/v1"
            elif "gpt" in lite_model: # Standard OpenAI models (gpt-4o, gpt-5-mini, etc.)
                api_key = os.getenv("OPENAI_API_KEY")
            
            # Fallback if no key matches logic (though should be covered)
            if not api_key:
                 # Default to OpenRouter if obscure
                 api_key = self.api_key_openrouter
                 api_base = "https://openrouter.ai/api/v1"
            
            # Prüfen, ob das Modell Structured Output unterstützt
            # Gemini und aktuelle OpenAI Modelle tun das.
            supports_schema = any(x in lite_model for x in ["gemini", "gpt-4", "gpt-3.5", "o1"])
            
            completion_args = {
                "model": lite_model,
                "messages": messages,
                "api_key": api_key,
                "api_base": api_base,
                "temperature": 0.85, 
                "max_tokens": 600
            }

            if supports_schema:
                # "Real" JSON Schema Enforcement via Pydantic
                completion_args["response_format"] = StoryResponse
            else:
                # Fallback für ältere/andere Modelle
                completion_args["response_format"] = {"type": "json_object"}

            # API-Aufruf
            response = completion(
                **completion_args,
                drop_params=True # Critical for models like o1/gpt-5 that restrict params
            )
            
            content = response.choices[0].message.content
            parsed = self._clean_json(content)
            
            # Validierung
            if not parsed or 'story' not in parsed or 'answer' not in parsed:
                print(f"Warnung: Ungültiges JSON erhalten: {content}")
                return get_fallback_scenario()
                
            return parsed

        except Exception as e:
            print(f"LLM Fehler: {e}")
            # Debug: Full Traceback in Server Log is helpful
            import traceback
            traceback.print_exc()
            return get_fallback_scenario()
