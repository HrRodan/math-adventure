import json
import re
import time
import os
from typing import Optional, Dict, List, Any
from litellm import completion
from pydantic import BaseModel, Field
from backend.prompts import get_system_prompt
from backend.config import get_provider_for_model, PROVIDERS

class StoryResponse(BaseModel):
    """
    Strukturiertes Ausgabeformat für fortlaufende Kapitel.
    Wird von LiteLLM/Pydantic genutzt, um ein valides JSON-Schema zu erzwingen.
    """
    story: str = Field(..., description="Der Text des nächsten Kapitels (100-150 Wörter).")
    question: str = Field(..., description="Die Matheaufgabe, die in die Story integriert ist.")
    answer: int = Field(..., description="Die numerische Lösung (Ganzzahl).")

class InitialStoryResponse(BaseModel):
    """
    Erweitertes Ausgabeformat für den Spielstart.
    Enthält zusätzlich den `story_arc`, der die langfristige Handlung plant.
    """
    story_arc: str = Field(..., description="Detaillierter Handlungsbogen (3-5 Sätze). Beschreibe das Ziel, den Antagonisten, den Ort und die Motivation der Helden genau. Dieser Text steuert die gesamte Zukunft.")
    story: str = Field(..., description="Kapitel 1 der Geschichte.")
    question: str = Field(..., description="Die Matheaufgabe.")
    answer: int = Field(..., description="Die numerische Lösung (Ganzzahl).")

class LLMEngine:
    """
    Zentrale Klasse für die Kommunikation mit LLMs.
    Kapselt LiteLLM, Provider-Routing, Fehlerbehandlung und JSON-Validierung.
    """
    def __init__(self):
        pass 

    def _clean_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Versucht, ein valides JSON-Objekt aus dem Antworttext zu extrahieren.
        Bewältigt Markdown-Blöcke (```json) und extrahiert den ersten gültigen JSON-Block.
        
        Args:
            text (str): Die rohe Antwort des LLMs.
            
        Returns:
            Optional[Dict]: Das geparste Dictionary oder None bei Fehlschlag.
        """
        try:
            # 1. Direkter Parse-Versuch
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except:
            # 2. Regex Fallback: Suche nach {...}
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return None

    def generate_turn(self, history: List[dict], model: str, theme: str = "Abenteuer", story_arc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generiert den nächsten Spielzug.
        
        Ablauf:
        1. Wählt den korrekten Provider und API-Key.
        2. Unterscheidet zwischen Start (leere History) und Fortsetzung.
        3. Baut den dynamischen User-Prompt zusammen (inklusive Story-Arc Erinnerung).
        4. Ruft das LLM mit Retry-Logik (Backoff) auf.
        
        Args:
            history (List[dict]): Liste der bisherigen Nachrichten (Format: [{'role': '...', 'content': '...'}])
            model (str): ID des zu nutzenden Modells.
            theme (str): Das Thema der Geschichte.
            story_arc (Optional[str]): Der langfristige Handlungsplan (nur bei Fortsetzung nötig).
            
        Returns:
            Optional[Dict]: Das generierte Antwort-Objekt oder None bei Fehler.
        """
        # --- 1. Provider Konfiguration laden ---
        provider = get_provider_for_model(model)
        if not provider:
            print(f"ERROR: Model '{model}' not configured.")
            return None

        api_key = provider.get_api_key()
        if not api_key:
            return None

        # --- 2. Modus bestimmen (Start vs. Fortsetzung) ---
        is_start = (len(history) == 0)
        
        # Wähle das passende Pydantic Schema
        response_schema = InitialStoryResponse if is_start else StoryResponse

        # --- 3. Prompt Engineering ---
        # Statischer System-Prompt (für Caching optimiert)
        system_msg = get_system_prompt()
        
        # Dynamischer User-Prompt
        if is_start:
            # Beim Start fordern wir die Erstellung des Story-Arcs an
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
            # Bei Fortsetzung bauen wir die Historie als Kontext ein
            hist_txt = "\n\n".join([f"Kapitel {i+1}: {m['content']}" for i, m in enumerate(history) if m['role'] == 'assistant'])
            
            # Der Story Arc wird als "Regieanweisung" eingefügt, damit das Modell den Faden nicht verliert
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

        # --- 4. LiteLLM Aufruf ---
        # Korrekte Modell-ID zusammensetzen (z.B. "openrouter/openai/gpt-4")
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
            "drop_params": True # Ignoriere Parameter, die das Modell nicht unterstützt
        }

        if provider.base_url: completion_args["api_base"] = provider.base_url
        if provider.extra_params: completion_args.update(provider.extra_params)

        print(f"DEBUG: Calling {lite_model} (Start={is_start})...")
        
        # Retry Loop mit exponentiellem Backoff (wichtig für API-Limits)
        for attempt in range(3):
            try:
                response = completion(**completion_args)
                content = response.choices[0].message.content
                parsed = self._clean_json(content)
                
                if parsed and 'story' in parsed:
                    # Fallback für fehlenden Arc beim Start (sollte dank Schema nicht passieren)
                    if is_start and 'story_arc' not in parsed:
                        parsed['story_arc'] = f"Abenteuer im Thema {theme}."
                    return parsed
            except Exception as e:
                print(f"Error (Attempt {attempt+1}): {e}")
                time.sleep(2 * (2**attempt)) # 2s, 4s, 8s

        return None
