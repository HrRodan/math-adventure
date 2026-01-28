import json
from backend.database import create_session, add_message, get_history
from backend.llm_engine import LLMEngine

class GameController:
    def __init__(self):
        self.llm = LLMEngine()

    def start_new_game(self, theme, model_name):
        """Creates a session and generates the first chapter."""
        session_id = create_session(theme, model_name)
        
        # Initial Prompt
        # Note: We don't save the very first system instructions as a user message
        # because the LLM engine handles the system prompt.
        
        # Call LLM
        response_data = self.llm.generate_turn([], model=model_name, theme=theme)
        
        # Save to DB. We store the full JSON response as a string for state.
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return session_id, response_data

    def submit_answer(self, session_id, user_answer, expected_answer, model_name, theme):
        """
        Validates answer. If correct, generates next chapter.
        """
        try:
            if int(user_answer) != int(expected_answer):
                return False, None
        except:
            return False, None

        # Answer is correct
        # 1. Update History with the success interaction
        add_message(session_id, "user", f"Ich habe das Rätsel gelöst! Die Antwort ist {user_answer}.")
        
        # 2. Get full history for context
        raw_history = get_history(session_id)
        
        # 3. Format history for the LLM
        formatted_history = []
        for m in raw_history:
            role = m['role']
            content = m['content']
            
            if role == "assistant":
                try:
                    data = json.loads(content)
                    clean_content = f"{data['story']}\n\nRätsel: {data['question']}"
                    formatted_history.append({"role": "assistant", "content": clean_content})
                except:
                    formatted_history.append({"role": "assistant", "content": content})
            else:
                formatted_history.append({"role": "user", "content": content})

        # 4. Generate Next
        response_data = self.llm.generate_turn(formatted_history, model=model_name, theme=theme)
        
        # 5. Save Next
        add_message(session_id, "assistant", json.dumps(response_data))
        
        return True, response_data

    def load_game(self, session_id):
        """Loads an existing session and restores the last state."""
        from backend.database import get_session_by_id, get_history
        theme, model_name = get_session_by_id(session_id)
        raw_history = get_history(session_id)
        
        # We need the last assistant message to get the expected answer
        last_assistant_msg = next((m for m in reversed(raw_history) if m['role'] == 'assistant'), None)
        
        if last_assistant_msg:
            try:
                response_data = json.loads(last_assistant_msg['content'])
            except:
                response_data = {"story": "Willkommen zurück!", "question": "Rechne 5+5 um zu starten", "answer": 10}
        else:
            response_data = {"story": "Willkommen zurück!", "question": "Rechne 5+5 um zu starten", "answer": 10}
            
        return theme, model_name, raw_history, response_data