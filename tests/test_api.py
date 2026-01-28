import time
import re
from gradio_client import Client

def solve_math(question_text):
    """Extrahiert Zahlen und löst einfache Matheaufgaben."""
    # Beispiel: "### ❓ Deine Aufgabe: 5 + 3 = ?"
    nums = [int(n) for n in re.findall(r'\d+', question_text)]
    if not nums: return 0
    
    # Einfache Heuristik für +, -, und Lücken
    if "+" in question_text:
        if "?" in question_text and question_text.index("?") < question_text.index("="):
             # 5 + ? = 8 -> 8 - 5
             return max(nums) - min(nums)
        else:
             # 5 + 3 = ?
             return nums[0] + nums[1]
    elif "-" in question_text:
        if "?" in question_text and question_text.index("?") < question_text.index("="):
             # 10 - ? = 4 -> 10 - 4
             return max(nums) - min(nums)
        else:
             # 10 - 4 = ?
             return nums[0] - nums[1]
    
    # Fallback für nur Text (sollte nicht vorkommen in v6)
    return nums[0] + nums[1] if len(nums) > 1 else nums[0]

def run_api_test():
    print("🚀 Starte API-Test mit Gradio Client...")
    
    client = Client("http://localhost:3000")
    
    # 1. Spiel starten
    print("\n--- SCHRITT 1: Spiel starten ---")
    result = client.predict(
        "Roboter im Dschungel", # Theme
        "gemini-2.0-flash",     # Model
        api_name="/start_game"
    )
    
    # Result Format: [session_id, answer, chat_history, question_label, input_reset, ...]
    print(f"DEBUG RESULT: {result}")
    
    session_id = result[0]
    expected_answer = result[1]
    chat_history = result[2]
    question_label = result[3]
    
    print(f"Session ID: {session_id}")
    print(f"Aufgabe: {question_label}")
    print(f"Erwartete Antwort (Server-Info): {expected_answer}")
    
    # 2. Aufgabe lösen
    # Für den Kohärenz-Test nutzen wir die Server-Antwort (Cheat Mode), 
    # damit wir garantiert weiterkommen.
    calculated_answer = expected_answer
    print(f"Nutze erwartete Antwort: {calculated_answer}")
    
    # 3. Antwort senden
    print("\n--- SCHRITT 2: Antwort senden ---")
    
    # Submit Answer Signatur: 
    # inputs=[answer_input, session_id, expected_answer, chat_history, theme, model]
    # outputs=[session_id, expected_answer, chat_history, math_label, input_reset, ...]
    
    result_turn2 = client.predict(
        str(calculated_answer), # User Input
        session_id,             # Session ID State
        expected_answer,        # Expected Answer State
        chat_history,           # Chat History State
        "Roboter im Dschungel", # Theme State
        "gemini-2.0-flash",     # Model State
        api_name="/submit_answer"
    )
    
    new_chat_history = result_turn2[2]
    new_question = result_turn2[3]
    
    # Letzte Nachricht im Chat prüfen (sollte die neue Story sein)
    # new_chat_history ist eine Liste von Dicts [{'role': 'user', ...}, {'role': 'assistant', ...}]
    last_msg = new_chat_history[-1]
    print(f"Neue Story: {last_msg['content'][:100]}...")
    print(f"Neue Aufgabe: {new_question}")
    
    if len(new_chat_history) > len(chat_history):
        print("\n✅ TEST ERFOLGREICH: Geschichte wurde fortgesetzt!")
    else:
        print("\n❌ TEST FEHLGESCHLAGEN: Keine neue Nachricht.")

if __name__ == "__main__":
    run_api_test()
