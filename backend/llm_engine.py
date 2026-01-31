import json
import re
import time
import random
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
                    return json.loads(match.group(0))
                except:
                    pass
            return None

    def generate_turn(self, history, model, theme="Abenteuer"):
        provider = get_provider_for_model(model)
        if not provider:
            # Fallback
            provider = PROVIDERS.get("google")
            model = provider.models[0]

        api_key = provider.get_api_key()
        if not api_key:
            return get_fallback_scenario()

        task_options = ["STANDARD", "GAP", "CHAIN", "TEXT", "SEQUENCE", "MONEY"]
        task_type = random.choice(task_options)
        
        # FIX: Statischer System Prompt ohne Argumente
        system_msg = get_system_prompt()
        
        # Dynamische Anweisungen in User Message
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

        # LiteLLM Prefix Logic
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

        if provider.base_url:
            completion_args["api_base"] = provider.base_url
        
        if provider.extra_params:
            completion_args.update(provider.extra_params)

        print(f"DEBUG: Sende an {lite_model}...")
        
        for attempt in range(2):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                if parsed and 'story' in parsed:
                    return parsed
            except Exception as e:
                print(f"Versuch {attempt+1} Fehler: {e}")
                time.sleep(1)

        return None