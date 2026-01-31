import json
import re
import time
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
                    return json.loads(match.group(0))
                except:
                    pass
            return None

    def generate_turn(self, history, model, theme="Abenteuer"):
        provider = get_provider_for_model(model)
        if not provider:
            # Fallback auf ersten verfügbaren Provider
            provider = list(PROVIDERS.values())[0]
            model = provider.models[0]

        api_key = provider.get_api_key()
        if not api_key:
            print(f"ERROR: No API Key for {provider.id}")
            return None

        # 1. System Prompt (Statisch mit vielen Beispielen)
        system_msg = get_system_prompt()
        
        # 2. User Prompt (Nur Kontext, keine starren Regeln)
        if not history:
            user_msg = f"THEMA: '{theme}'\n\nFühre die Helden ein, starte das Abenteuer und stelle das erste Mathe-Rätsel!"
        else:
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            user_msg = f"THEMA: '{theme}'\n\nWAS BISHER GESCHAH:\n{hist_txt}\n\nErzähle weiter und integriere ein passendes Mathe-Rätsel in die Handlung."

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        # Modell-ID & Params
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
            "drop_params": True
        }

        if provider.base_url:
            completion_args["api_base"] = provider.base_url
        
        if provider.extra_params:
            completion_args.update(provider.extra_params)

        print(f"DEBUG: LiteLLM Call -> model='{lite_model}'")
        
        try:
            response = completion(**completion_args)
            content = response.choices[0].message.content
            parsed = self._clean_json(content)
            if parsed and 'story' in parsed:
                return parsed
        except Exception as e:
            print(f"ERROR calling {lite_model}: {e}")
            import traceback
            traceback.print_exc()

        return None
