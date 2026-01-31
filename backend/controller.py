import json
from typing import Tuple, Dict, Any, Union, List, Optional
from backend.database import create_session, add_message, get_history, SessionLocal, GameSession, get_session_details, update_story_arc
from backend.llm_engine import LLMEngine

class GameController:
    """
    Der 'Regisseur' des Spiels (Controller-Layer).
    
    Verantwortlichkeiten:
    - Koordiniert UI-Eingaben und Datenbank-Operationen.
    - Ruft die LLM-Engine auf.
    - Verwaltet den Spielzustand (Session, Stars - deprecated, Story Arc).
    """
    
    def __init__(self):
        self.llm = LLMEngine()

    def start_new_game(self, theme: str, model_name: str) -> Tuple[Union[int, None], Dict[str, Any], str]:
        """
        Startet ein neues Spiel, initialisiert die Session und generiert Kapitel 1.
        
        Args:
            theme (str): Das vom User gewählte Thema.
            model_name (str): Das gewählte KI-Modell.
            
        Returns:
            Tuple[int, Dict, str]: (session_id, response_data, story_arc).
                                   Bei Fehler ist response_data ein Fehler-Dict.
        """
        # 1. Session in DB anlegen
        session_id = create_session(theme, model_name)
        
        # 2. Erstes Kapitel generieren (History ist leer)
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        if not response_data:
            return session_id, {
                "story": "Der Erzähler hat den Faden verloren. Bitte versuche es gleich nochmal!", 
                "question": "Fehler beim Start", 
                "answer": 0
            }, "Fehler"

        # 3. Story Arc extrahieren und speichern
        # Der Arc ist wichtig für die Kohärenz zukünftiger Kapitel
        arc = response_data.get('story_arc', "Kein Plan vorhanden.")
        update_story_arc(session_id, arc)

        # 4. Antwort persistieren
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return session_id, response_data, arc

    def submit_answer(self, session_id: int, user_answer: str, expected_answer: str, model_name: str, theme: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verarbeitet die Antwort des Benutzers auf ein Mathe-Rätsel.
        
        Ablauf:
        1. Validiert die Antwort (Vergleich User vs. Expected).
        2. Speichert User-Nachricht.
        3. Lädt Kontext (History + Story Arc).
        4. Generiert nächstes Kapitel via LLM.
        
        Args:
            session_id (int): ID der aktuellen Session.
            user_answer (str): Eingabe des Benutzers.
            expected_answer (str): Die korrekte Lösung (als String gespeichert).
            model_name (str): Modell-ID.
            theme (str): Thema.
            
        Returns:
            Tuple[bool, Dict]: (Erfolg_Status, Antwort_Daten).
        """
        # 1. Einfache Validierung (String zu Int Konvertierung)
        try:
            if int(user_answer) != int(expected_answer):
                return False, None
        except:
            return False, None

        # 2. User-Nachricht speichern
        add_message(session_id, "user", f"Ich habe das Rätsel gelöst! Die Antwort ist {user_answer}.")
        
        # 3. Kontext laden
        # Wir benötigen die rohe History für den Prompt und den Arc für die Regieanweisung
        raw_history = get_history(session_id)
        _, _, story_arc = get_session_details(session_id)
        
        # Konvertierung für LLM Engine (obwohl get_history schon dicts liefert, hier explizit zur Sicherheit)
        formatted_history = [{"role": m['role'], "content": m['content']} for m in raw_history]

        # 4. Nächstes Kapitel anfragen
        response_data = self.llm.generate_turn(
            formatted_history, 
            model=model_name, 
            theme=theme, 
            story_arc=story_arc
        )
        
        if not response_data:
            # Bei API-Fehler: Wir behalten den 'answer' Wert bei, damit der User retryen kann
            return True, {
                "story": "Huch, die Tinte ist alle! Klicke bitte nochmal auf 'Prüfen'.", 
                "question": "Warte auf Antwort...", 
                "answer": expected_answer 
            }

        # 5. Speichern
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return True, response_data

    def load_game(self, session_id: int) -> Tuple[str, str, List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Lädt eine existierende Session wiederher.
        
        Returns:
            Tuple: (Thema, Modell, Verlauf, Letzte_Antwort_Daten, Story_Arc).
        """
        theme, model_name, arc = get_session_details(session_id)
        raw_history = get_history(session_id)
        
        # Wir müssen den 'State' der letzten Runde wiederherstellen (Frage, Antwort)
        # Dazu parsen wir die allerletzte Nachricht des Assistenten.
        last_assistant_msg = next((m for m in reversed(raw_history) if m['role'] == 'assistant'), None)
        
        if last_assistant_msg:
            try:
                response_data = json.loads(last_assistant_msg['content'])
            except:
                # Fallback bei korruptem JSON
                response_data = {"story": "Willkommen zurück!", "question": "...", "answer": 0}
        else:
            response_data = {"story": "Start...", "question": "...", "answer": 0}
            
        return theme, model_name, raw_history, response_data, arc