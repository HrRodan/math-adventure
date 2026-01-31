import json
from backend.database import create_session, add_message, get_history, SessionLocal, GameSession, get_session_details, update_story_arc
from backend.llm_engine import LLMEngine

class GameController:
    """
    Der 'Regisseur' des Spiels. 
    Verbindet UI, Datenbank und KI-Engine.
    """
    
    def __init__(self):
        self.llm = LLMEngine()

    def start_new_game(self, theme, model_name):
        """
        Initialisiert ein neues Spiel.
        
        Returns:
            tuple: (session_id, antwort_daten, story_arc)
        """
        session_id = create_session(theme, model_name)
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        if not response_data:
            return session_id, {
                "story": "Der Erzähler hat den Faden verloren. Bitte versuche es gleich nochmal!", 
                "question": "Fehler beim Start", 
                "answer": 0
            }, "Fehler"

        arc = response_data.get('story_arc', "Kein Plan vorhanden.")
        update_story_arc(session_id, arc)

        add_message(session_id, "assistant", json.dumps(response_data))
        
        return session_id, response_data, arc

    def submit_answer(self, session_id, user_answer, expected_answer, model_name, theme):
        """
        Verarbeitet die Antwort des Kindes.
        """
        try:
            if int(user_answer) != int(expected_answer):
                return False, None
        except:
            return False, None

        # Antwort korrekt -> Verlauf aktualisieren
        add_message(session_id, "user", f"Ich habe das Rätsel gelöst! Die Antwort ist {user_answer}.")
        
        # Kontext laden
        raw_history = get_history(session_id)
        _, _, story_arc = get_session_details(session_id)
        
        formatted_history = [{"role": m['role'], "content": m['content']} for m in raw_history]

        # KI fragen
        response_data = self.llm.generate_turn(
            formatted_history, 
            model=model_name, 
            theme=theme, 
            story_arc=story_arc
        )
        
        if not response_data:
            return True, {
                "story": "Huch, die Tinte ist alle! Klicke bitte nochmal auf 'Prüfen'.", 
                "question": "Warte auf Antwort...", 
                "answer": expected_answer 
            }

        # Speichern
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return True, response_data

    def load_game(self, session_id):
        """
        Lädt eine Session.
        """
        theme, model_name, arc = get_session_details(session_id)
        raw_history = get_history(session_id)
        
        last_assistant_msg = next((m for m in reversed(raw_history) if m['role'] == 'assistant'), None)
        
        if last_assistant_msg:
            try:
                response_data = json.loads(last_assistant_msg['content'])
            except:
                response_data = {"story": "Willkommen zurück!", "question": "...", "answer": 0}
        else:
            response_data = {"story": "Willkommen zurück!", "question": "...", "answer": 0}
            
        return theme, model_name, raw_history, response_data, arc
