import json
import re
import time
import random
import os
from litellm import completion
from pydantic import BaseModel, Field
from backend.prompts import get_system_prompt, get_fallback_scenario
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
            provider = PROVIDERS.get("google")
            model = provider.models[0]

        api_key = provider.get_api_key()
        if not api_key:
            print(f"WARNUNG: Kein API Key für {provider.id} gefunden.")
            return get_fallback_scenario()

        # System- und User-Prompts vorbereiten
        system_msg = get_system_prompt()
        
        task_options = ["STANDARD", "GAP", "CHAIN", "TEXT", "SEQUENCE", "MONEY"]
        task_type = random.choice(task_options)
        
        instructions = f"""
        THEMA: "{theme}"
        AUFGABENTYP: {task_type}
        
        Beispiele:
        - "12 Goldmünzen, 5 verloren. Wie viele bleiben?"
        - "Ein Zauberstab kostet 8 Kristalle. Wie viel kosten 2?"
        
        Nutze keine Aufgaben mit 0.
        """
        
        if not history:
            user_msg = f"START EINER NEUEN GESCHICHTE.\n{instructions}\n\nFühre Helden ein."
        else:
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            user_msg = f"FORTSETZUNG.\nWAS BISHER GESCHAH:\n{hist_txt}\n\nANWEISUNG:\n{instructions}\n\nErzähle weiter!"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        # Modell-ID für LiteLLM konstruieren
        if provider.litellm_prefix and not model.startswith(provider.litellm_prefix):
            lite_model = f"{provider.litellm_prefix}{model}"
        else:
            lite_model = model

        completion_args = {
            "model": lite_model,
            "messages": messages,
            "api_key": api_key,
            "temperature": 0.85,
            "max_tokens": 800,
            "response_format": StoryResponse
        }

        # Falls eine Base URL konfiguriert ist (z.B. OpenRouter ohne Prefix-Auto-Detection)
        if provider.base_url:
            completion_args["api_base"] = provider.base_url
        
        if provider.extra_params:
            completion_args.update(provider.extra_params)

        print(f"DEBUG: LiteLLM Call -> model='{lite_model}'")
        
        for attempt in range(2):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                if parsed and 'story' in parsed:
                    return parsed
            except Exception as e:
                print(f"Versuch {attempt+1} Fehler mit {lite_model}: {e}")
                time.sleep(1)

        return None
