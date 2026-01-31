import json
import re
import time
import random
import os
from litellm import completion
from pydantic import BaseModel, Field
from backend.prompts import get_system_prompt
from backend.config import get_provider_for_model, PROVIDERS

class StoryResponse(BaseModel):
    """
    Strukturiertes Ausgabeformat für das LLM.
    Wird von LiteLLM/Pydantic genutzt, um ein valides JSON-Schema zu erzwingen.
    """
    story: str = Field(..., description="Der Text des nächsten Kapitels (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe.")
    answer: int = Field(..., description="Die numerische Lösung (Ganzzahl).")

class LLMEngine:
    """
    Zentrale Klasse für die Kommunikation mit LLMs.
    Kapselt LiteLLM, Provider-Routing, Fehlerbehandlung und JSON-Validierung.
    """
    def __init__(self):
        pass 

    def _clean_json(self, text):
        """
        Versucht, aus einem rohen String ein valides JSON-Objekt zu extrahieren.
        
        Args:
            text (str): Die Antwort des LLMs (kann Markdown-Blöcke ```json enthalten).
            
        Returns:
            dict | None: Das geparste JSON-Objekt oder None bei Fehler.
        """
        try:
            # 1. Direkter Versuch
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except:
            # 2. Fallback: Suche nach {...} Muster mittels Regex
            # Dies hilft, wenn das LLM Text vor oder nach dem JSON schreibt.
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return None

    def generate_turn(self, history, model, theme="Abenteuer"):
        """
        Generiert den nächsten Spielzug (Story + Rätsel).
        
        Ablauf:
        1. Identifiziert den Provider und lädt den API-Key.
        2. Baut den Prompt (Statischer System-Teil + Dynamischer User-Teil).
        3. Sendet Request mit Retry-Logik (Exponential Backoff).
        4. Validiert das JSON-Ergebnis.
        
        Args:
            history (list): Liste der bisherigen Nachrichten (für Kontext).
            model (str): Name des zu verwendenden Modells.
            theme (str): Das Thema der Geschichte.
            
        Returns:
            dict | None: {'story': ..., 'question': ..., 'answer': ...} oder None bei Totalausfall.
        """
        # --- 1. Provider Setup ---
        provider = get_provider_for_model(model)
        if not provider:
            print(f"ERROR: Model '{model}' not configured.")
            return None

        api_key = provider.get_api_key()
        if not api_key:
            print(f"ERROR: No API Key for {provider.id}")
            return None

        # --- 2. Prompt Engineering ---
        # Statischer System-Prompt für besseres Caching
        system_msg = get_system_prompt()
        
        # Dynamischer User-Prompt (Few-Shot Beispiele)
        task_options = ["STANDARD", "GAP", "CHAIN", "TEXT", "SEQUENCE", "MONEY"]
        task_type = random.choice(task_options)
        
        instructions = f"""
        THEMA: "{theme}"
        AUFGABENTYP: {task_type}
        
        Beispiele:
        - "3 Kisten hier, 8 dort. Wie viele total?" (Standard)
        - "Wir haben 9m Seil, brauchen 15m. Wie viel fehlt?" (Lücke) 
        
        Wichtig: Nutze KEINE 0-Aufgaben. Währung passend zur Story (Gold, Kristalle, Smaragde).
        """
        
        if not history:
            user_msg = f"START EINER NEUEN GESCHICHTE.\n{instructions}\n\nFühre Helden ein."
        else:
            # Wir bauen die Historie als Text zusammen, statt message-Objekte zu übergeben.
            # Das ist oft robuster bei Modell-Wechseln.
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            user_msg = f"FORTSETZUNG.\nWAS BISHER GESCHAH:\n{hist_txt}\n\nANWEISUNG:\n{instructions}\n\nErzähle weiter!"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        # --- 3. Modell-Parameter ---
        # Konstruktion der LiteLLM-Modell-ID (z.B. "openrouter/openai/gpt-4")
        if provider.litellm_prefix and not model.startswith(provider.litellm_prefix):
            lite_model = f"{provider.litellm_prefix}{model}"
        else:
            lite_model = model

        completion_args = {
            "model": lite_model,
            "messages": messages,
            "api_key": api_key,
            "max_tokens": 800,
            "response_format": StoryResponse,
            "drop_params": True # Ignoriert nicht unterstützte Parameter (z.B. bei o1)
        }

        if provider.base_url:
            completion_args["api_base"] = provider.base_url
        
        if provider.extra_params:
            completion_args.update(provider.extra_params)

        print(f"DEBUG: LiteLLM Call -> model='{lite_model}'")
        
        # --- 4. Ausführung mit Retry & Backoff ---
        for attempt in range(3):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                
                if parsed and 'story' in parsed:
                    return parsed
                else:
                    print(f"Warning (Attempt {attempt+1}): Invalid JSON received.")
            except Exception as e:
                print(f"Error (Attempt {attempt+1}) calling {lite_model}: {e}")
                # Exponentielles Backoff: 2s -> 4s -> 8s
                # Hilft besonders bei 503 Overloaded Fehlern
                sleep_time = 2 * (2 ** attempt)
                time.sleep(sleep_time)

        print("CRITICAL: All attempts failed.")
        return None
