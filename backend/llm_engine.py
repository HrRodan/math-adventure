import json
import re
import time
import os
from litellm import completion
from pydantic import BaseModel, Field
from backend.prompts import get_system_prompt
from backend.config import get_provider_for_model, PROVIDERS

class StoryResponse(BaseModel):
    """Standard-Antwort für fortlaufende Kapitel."""
    story: str = Field(..., description="Der Text des nächsten Kapitels (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe.")
    answer: int = Field(..., description="Die numerische Lösung (Ganzzahl).")

class InitialStoryResponse(BaseModel):
    """Antwort für den Start: Enthält zusätzlich den Handlungsbogen."""
    story_arc: str = Field(..., description="Detaillierter Handlungsbogen (3-5 Sätze). Beschreibe das Ziel, den Antagonisten, den Ort und die Motivation der Helden genau. Dieser Text steuert die gesamte Zukunft.")
    story: str = Field(..., description="Kapitel 1 der Geschichte.")
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

    def generate_turn(self, history, model, theme="Abenteuer", story_arc=None):
        provider = get_provider_for_model(model)
        if not provider: return None
        api_key = provider.get_api_key()
        if not api_key: return None

        is_start = (len(history) == 0)
        response_schema = InitialStoryResponse if is_start else StoryResponse
        system_msg = get_system_prompt()
        
        if is_start:
            user_msg = f"""
            START EINER NEUEN GESCHICHTE.
            THEMA: "{theme}"
            
            AUFGABE:
            1. PLANUNG: Entwirf einen internen Handlungsbogen (Story Arc): Wer ist der Held? Was ist das große Ziel? Wer ist der Gegenspieler?
            2. TEXT: Schreibe Kapitel 1.
               ACHTUNG: Der Leser sieht deinen Plan NICHT. Du musst die Helden und die Ausgangssituation im Erzähltext ("story") sauber einführen! Starte nicht mitten drin.
            3. MATHE: Stelle das erste Mathe-Rätsel passend zur Situation.
            """
        else:
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            
            arc_instruction = ""
            if story_arc:
                arc_instruction = f"\n\nWICHTIG - DEINE MISSION (ROTER FADEN):\n{story_arc}\nOrientiere dich an diesem Ziel, aber übereile nichts."
            
            user_msg = f"""
            THEMA: "{theme}"
            {arc_instruction}
            
            HINWEIS: Der Leser kennt den Story Arc NICHT. Wenn neue Figuren (wie der Schurke) auftreten, führe sie im Text für den Leser ein. Setze kein Wissen voraus, das nicht in "WAS BISHER GESCHAH" steht.
            
            WAS BISHER GESCHAH:
            {hist_txt}
            
            ANWEISUNG:
            Erzähle die Geschichte weiter und integriere ein passendes Mathe-Rätsel.
            """

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
            "max_tokens": 1000,
            "response_format": response_schema,
            "drop_params": True
        }

        if provider.base_url: completion_args["api_base"] = provider.base_url
        if provider.extra_params: completion_args.update(provider.extra_params)

        print(f"DEBUG: Calling {lite_model} (Start={is_start})...")
        
        for attempt in range(3):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                if parsed and 'story' in parsed:
                    if is_start and 'story_arc' not in parsed:
                        parsed['story_arc'] = f"Abenteuer im Thema {theme}."
                    return parsed
            except Exception as e:
                print(f"Error ({attempt+1}): {e}")
                time.sleep(2 * (2**attempt))

        return None