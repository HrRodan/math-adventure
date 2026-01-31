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
    story: str = Field(..., description="Der Text des nächsten Kapitels (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe.")
    answer: int = Field(..., description="Die numerische Lösung (Ganzzahl).")

class LLMEngine:
    def __init__(self):
        pass 

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

    def generate_turn(self, history, model, theme="Abenteuer"):
        provider = get_provider_for_model(model)
        if not provider:
            print(f"FEHLER: Modell '{model}' nicht in Config gefunden.")
            return None # KEIN FALLBACK

        api_key = provider.get_api_key()
        if not api_key:
            print(f"FEHLER: Kein API Key für {provider.id} ({provider.api_key_env})")
            return None

        # System-Prompt
        system_msg = get_system_prompt()
        
        # User-Prompt
        task_options = ["STANDARD", "GAP", "CHAIN", "TEXT", "SEQUENCE", "MONEY"]
        task_type = random.choice(task_options)
        
        instructions = f"""
        THEMA: "{theme}"
        AUFGABENTYP: {task_type}
        
        Beispiele:
        - "3 Kisten hier, 8 dort. Wie viele total?" (Standard)
        - "Wir haben 9m Seil, brauchen 15m. Wie viel fehlt?" (Lücke)
        - "Ein Rubin kostet 5 Gold. Wie viel kosten 3?" (Sachaufgabe)
        
        Nutze KEINE Aufgaben mit 0.
        """
        
        if not history:
            user_msg = f"START EINER NEUEN GESCHICHTE.\n{instructions}\n\nFühre Helden und Ziel ein."
        else:
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            user_msg = f"FORTSETZUNG.\nWAS BISHER GESCHAH:\n{hist_txt}\n\nANWEISUNG:\n{instructions}\n\nErzähle weiter!"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        # Modell-ID bauen
        if provider.litellm_prefix and not model.startswith(provider.litellm_prefix):
            lite_model = f"{provider.litellm_prefix}{model}"
        else:
            lite_model = model

        completion_args = {
            "model": lite_model,
            "messages": messages,
            "api_key": api_key,
            # "temperature": 0.85,  <- ENTFERNT, da gpt-5 das nicht mag
            "max_tokens": 800,
            "response_format": StoryResponse,
            "drop_params": True # Wichtig für strikte Modelle
        }

        if provider.base_url:
            completion_args["api_base"] = provider.base_url
        
        if provider.extra_params:
            completion_args.update(provider.extra_params)

        print(f"DEBUG: Sende an {lite_model}...")
        
        # Einziger Versuch (Kein Retry-Spam bei Konfig-Fehlern)
        try:
            response = completion(**completion_args)
            content = response.choices[0].message.content
            parsed = self._clean_json(content)
            if parsed and 'story' in parsed:
                return parsed
            else:
                print(f"FEHLER: Ungültiges JSON von {model}: {content}")
        except Exception as e:
            print(f"CRITICAL ERROR mit {model}: {e}")
            import traceback
            traceback.print_exc()

        return None