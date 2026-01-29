import json
from backend.database import create_session, add_message, get_history, SessionLocal, GameSession, get_session_by_id
from backend.llm_engine import LLMEngine

class GameController:
    def __init__(self):
        self.llm = LLMEngine()

    def start_new_game(self, theme, model_name):
        """Erstellt eine neue Sitzung und generiert das erste Kapitel."""
        session_id = create_session(theme, model_name)
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        if not response_data:
            return session_id, {
                "story": "Der Erzähler hat den Faden verloren. Bitte versuche es gleich nochmal!", 
                "question": "Fehler beim Start", 
                "answer": 0
            }, 0

        add_message(session_id, "assistant", json.dumps(response_data))
        return session_id, response_data, 0

    def submit_answer(self, session_id, user_answer, expected_answer, model_name, theme):
        """Überprüft die Antwort und generiert bei Erfolg das nächste Kapitel."""
        try:
            if int(user_answer) != int(expected_answer):
                return False, None, 0
        except:
            return False, None, 0

        # Antwort ist korrekt -> Stern vergeben
        db = SessionLocal()
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        session.stars += 1
        new_stars = session.stars
        db.commit()
        db.close()

        # Erfolgreiche Lösung in die DB schreiben
        add_message(session_id, "user", f"Ich habe das Rätsel gelöst! Die Antwort ist {user_answer}.")
        
        # Historie laden
        raw_history = get_history(session_id)
        formatted_history = []
        for m in raw_history:
            formatted_history.append({"role": m['role'], "content": m['content']})

        # Nächstes Kapitel generieren
        response_data = self.llm.generate_turn(formatted_history, model=model_name, theme=theme)
        
        if not response_data:
            # Bei Fehlern: Wir geben eine Meldung zurück, behalten aber die 'expected_answer'.
            # Der User kann dann einfach nochmal klicken.
            return True, {
                "story": "Huch, die Tinte ist alle! Klicke bitte nochmal auf 'Prüfen'.", 
                "question": "Warte auf Antwort...", 
                "answer": expected_answer # Wichtig: Alte Antwort bleibt aktiv
            }, new_stars

        # Erfolg: Speichern
        add_message(session_id, "assistant", json.dumps(response_data))
        return True, response_data, new_stars

    def load_game(self, session_id):
        """Lädt eine bestehende Sitzung."""
        theme, model_name = get_session_by_id(session_id)
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
                response_data = {"story": "Willkommen zurück!", "question": "Rechne 5+5 um zu starten", "answer": 10}
        else:
            response_data = {"story": "Willkommen zurück!", "question": "Rechne 5+5 um zu starten", "answer": 10}
            
        return theme, model_name, raw_history, response_data, stars