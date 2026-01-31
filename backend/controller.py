import json
from backend.database import create_session, add_message, get_history, SessionLocal, GameSession, get_session_details, update_story_arc
from backend.llm_engine import LLMEngine

class GameController:
    def __init__(self):
        self.llm = LLMEngine()

    def start_new_game(self, theme, model_name):
        """Startet Spiel und initialisiert den Story-Arc."""
        session_id = create_session(theme, model_name)
        
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        if not response_data:
            return session_id, {
                "story": "Der Erzähler schweigt...", "question": "Fehler", "answer": 0
            }, 0

        # Story Arc speichern & extrahieren
        arc = response_data.get('story_arc', "Kein Plan vorhanden.")
        update_story_arc(session_id, arc)

        add_message(session_id, "assistant", json.dumps(response_data))
        return session_id, response_data, 0, arc # Return ARC

    def submit_answer(self, session_id, user_answer, expected_answer, model_name, theme):
        try:
            if int(user_answer) != int(expected_answer):
                return False, None, 0
        except:
            return False, None, 0

        db = SessionLocal()
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        session.stars += 1
        new_stars = session.stars
        db.commit()
        db.close()

        add_message(session_id, "user", f"Gelöst! Antwort: {user_answer}")
        
        raw_history = get_history(session_id)
        _, _, story_arc = get_session_details(session_id)
        
        formatted_history = [{"role": m['role'], "content": m['content']} for m in raw_history]

        response_data = self.llm.generate_turn(
            formatted_history, 
            model=model_name, 
            theme=theme, 
            story_arc=story_arc
        )
        
        if not response_data:
            return True, {
                "story": "Verbindungsproblem...", "question": "...", "answer": expected_answer
            }, new_stars

        add_message(session_id, "assistant", json.dumps(response_data))
        return True, response_data, new_stars

    def load_game(self, session_id):
        theme, model, arc = get_session_details(session_id) # Arc holen
        raw_history = get_history(session_id)
        
        db = SessionLocal()
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        stars = session.stars
        db.close()
        
        last_assistant_msg = next((m for m in reversed(raw_history) if m['role'] == 'assistant'), None)
        if last_assistant_msg:
            try:
                response_data = json.loads(last_assistant_msg['content'])
            except:
                response_data = {"story": "Weiter geht's!", "question": "...", "answer": 0}
        else:
            response_data = {"story": "Start...", "question": "...", "answer": 0}
            
        return theme, model, raw_history, response_data, stars, arc # Return ARC
