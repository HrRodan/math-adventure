import os
import json
import random
import re
import time
from litellm import completion
from dotenv import load_dotenv
from backend.prompts import get_system_prompt
from pydantic import BaseModel, Field

# Umgebungsvariablen laden
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Definition des erwarteten Schemas
class StoryResponse(BaseModel):
    story: str = Field(..., description="Der Text des nächsten Kapitels der Geschichte (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe, die das Kind lösen muss.")
    answer: int = Field(..., description="Die numerische Lösung der Aufgabe (Ganzzahl).")

class LLMEngine:
    def __init__(self):
        self.api_key_google = os.getenv("GEMINI_API_KEY")
        self.api_key_openrouter = os.getenv("OPENROUTER_API_KEY")
        
    def _clean_json(self, text):
        try:
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except:
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
        Generiert das nächste Kapitel.
        Nutzt statischen System-Prompt für Caching.
        Packt dynamische Infos in den User-Prompt.
        """
        
        # System-Prompt (Statisch für Caching)
        system_instructions = get_system_prompt()
        
        # User-Prompt (Dynamisch)
        # Hier geben wir Few-Shot Beispiele für gute Aufgaben
        math_examples = """
        BEISPIELE FÜR GUTE AUFGABEN (Variiere den Typ passend zur Situation!):
        - Situation: Helden finden Kisten. -> "3 Kisten hier, 8 dort. Wie viele total?" (Standard)
        - Situation: Brücke fehlt ein Stück. -> "Die Brücke muss 15m lang sein, wir haben 9m. Wie viel fehlt?" (Lücke)
        - Situation: Monster greifen an. -> "2 Wellen mit je 4 Monstern." (Multiplikation)
        - Situation: Schatzkammer. -> "Ein Rubin ist 5 Goldstücke wert. Wie viel sind 3 Rubine?" (Währung/Sachaufgabe)
        - Situation: Code-Schloss. -> "Die Zahlenfolge geht: 3, 6, 9... wie heißt die nächste?" (Reihe)
        
        WICHTIG: Nutze KEINE Aufgaben mit 0 (z.B. 5+0). Fordere das Kind! (Zehnerübergang ok).
        """

        if not history:
            user_message = f"""
            START EINER NEUEN GESCHICHTE.
            Thema: "{theme}"
            
            Anweisung:
            1. Führe Helden und Ziel ein.
            2. Schreibe Kapitel 1.
            3. {math_examples}
            """
        else:
            # Wir bauen die Historie in den User-Prompt ein
            # (Bei manchen Modellen besser als separate Messages für Caching)
            history_text = "\n\n".join([f"Kapitel {i+1}: {msg['content']}" for i, msg in enumerate(history) if msg['role'] == 'assistant'])
            
            user_message = f"""
            FORTSETZUNG.
            
            WAS BISHER GESCHAH:
            {history_text}
            
            ANWEISUNG:
            Erzähle weiter. Bleib beim Thema "{theme}".
            {math_examples}
            """

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_message}
        ]
        
        # Modell-Setup
        lite_model = model
        if "gemini" in model and not model.startswith("gemini/"):
            lite_model = f"gemini/{model}"
        elif "gpt" in model and not model.startswith("openai/"):
            lite_model = f"openai/{model}"

        api_key = None
        api_base = None
        
        if "gemini" in lite_model:
            api_key = self.api_key_google
        elif "openrouter" in lite_model or "gpt-oss" in lite_model:
            api_key = self.api_key_openrouter
            api_base = "https://openrouter.ai/api/v1"
        elif "gpt" in lite_model:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Fallback
            api_key = self.api_key_openrouter
            api_base = "https://openrouter.ai/api/v1"

        supports_schema = any(x in lite_model for x in ["gemini", "gpt-4", "gpt-3.5", "o1"])
        
        completion_args = {
            "model": lite_model,
            "messages": messages,
            "api_key": api_key,
            "api_base": api_base,
            "temperature": 0.85, 
            "max_tokens": 800,
            "drop_params": True 
        }

        if supports_schema:
            completion_args["response_format"] = StoryResponse
        else:
            completion_args["response_format"] = {"type": "json_object"}

        # Retry Loop (3 Versuche)
        for attempt in range(3):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                
                if parsed and 'story' in parsed and 'answer' in parsed:
                    return parsed
                else:
                    print(f"Versuch {attempt+1}: Ungültiges JSON: {content}")
            
            except Exception as e:
                print(f"Versuch {attempt+1}: API Fehler: {e}")
                time.sleep(1) # Kurze Pause

        # Wenn alles scheitert: KEIN Fallback, sondern None (Controller wirft Fehler)
        return None