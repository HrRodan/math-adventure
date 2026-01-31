import json
from backend.database import create_session, add_message, get_history, SessionLocal, GameSession, get_session_by_id
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
            tuple: (session_id, antwort_daten, sterne)
        """
        session_id = create_session(theme, model_name)
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        if not response_data:
            # Fehlerfall: Wir speichern NICHTS in der DB, damit die Session sauber bleibt.
            return session_id, {
                "story": "Der Erzähler hat den Faden verloren. Bitte versuche es gleich nochmal!", 
                "question": "Fehler beim Start", 
                "answer": 0
            }, 0

        # Nur valide Antworten werden persistiert
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return session_id, response_data, 0

    def submit_answer(self, session_id, user_answer, expected_answer, model_name, theme):
        """
        Verarbeitet die Antwort des Kindes.
        
        Logik:
        1. Validierung (Ist die Zahl korrekt?)
        2. Bei Erfolg: Stern vergeben, User-Nachricht speichern.
        3. Nächstes Kapitel generieren.
        4. Bei KI-Fehler: User-Nachricht bleibt, aber kein neues Kapitel. User kann 'Retry' machen.
        """
        try:
            if int(user_answer) != int(expected_answer):
                return False, None, 0
        except:
            return False, None, 0

        # 1. Stern vergeben (Transaktion)
        db = SessionLocal()
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        session.stars += 1
        new_stars = session.stars
        db.commit()
        db.close()

        # 2. Verlauf aktualisieren
        add_message(session_id, "user", f"Ich habe das Rätsel gelöst! Die Antwort ist {user_answer}.")
        
        # 3. Kontext laden
        raw_history = get_history(session_id)
        formatted_history = []
        for m in raw_history:
            formatted_history.append({"role": m['role'], "content": m['content']})

        # 4. KI fragen
        response_data = self.llm.generate_turn(formatted_history, model=model_name, theme=theme)
        
        if not response_data:
            # Fehler: Wir geben die ALTE expected_answer zurück.
            # So kann der User einfach nochmal "Prüfen" klicken, um die KI neu anzustupsen.
            return True, {
                "story": "Huch, die Tinte ist alle! Klicke bitte nochmal auf 'Prüfen'.", 
                "question": "Warte auf Antwort...", 
                "answer": expected_answer 
            }, new_stars

        # 5. Speichern
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return True, response_data, new_stars

    def load_game(self, session_id):
        """
        Lädt eine Session und stellt den letzten Spielzustand wieder her.
        Wichtig: Extrahiert die letzte Frage/Antwort aus dem JSON-History-Log.
        """
        theme, model_name = get_session_by_id(session_id)
        raw_history = get_history(session_id)
        
        db = SessionLocal()
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        stars = session.stars
        db.close()
        
        # Suche die letzte Nachricht der KI
        last_assistant_msg = next((m for m in reversed(raw_history) if m['role'] == 'assistant'), None)
        
        if last_assistant_msg:
            try:
                response_data = json.loads(last_assistant_msg['content'])
            except:
                response_data = {"story": "Willkommen zurück!", "question": "...", "answer": 0}
        else:
            response_data = {"story": "Willkommen zurück!", "question": "...", "answer": 0}
            
        return theme, model_name, raw_history, response_data, stars
