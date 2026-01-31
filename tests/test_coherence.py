import sys
import os
import re
import time

# Add root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.controller import GameController

def run_simulation():
    print("🤖 Starte autonome Agenten-Simulation (Kohärenz-Test)...")
    controller = GameController()
    theme = "Pirateninsel"
    model = "gemini-3-flash-preview"
    
    # Start
    print(f"--- RUNDE 1 ---")
    session_id, data, stars = controller.start_new_game(theme, model)
    
    if not data or 'answer' not in data:
        print("❌ Simulation abgebrochen: Kein Start-Data.")
        return

    expected = data['answer']
    print(f"Geschichte: {data['story'][:100]}...")
    print(f"Aufgabe: {data['question']} (Lösung: {expected})")
    
    for i in range(2, 6): # Wir testen 5 Runden zur schnellen Verifizierung
        print(f"\n--- RUNDE {i} ---")
        
        # Simuliere Benutzereingabe
        user_answer = str(expected) 
        
        success, new_data, current_stars = controller.submit_answer(session_id, user_answer, expected, model, theme)
        
        if not success or not new_data:
            print("❌ Simulation fehlgeschlagen: KI-Antwort fehlt oder Antwort abgelehnt.")
            break
            
        expected = new_data['answer']
        print(f"Geschichte: {new_data['story'][:100]}...")
        print(f"Aufgabe: {new_data['question']} (Lösung: {expected})")
        print(f"Sterne: {current_stars}")
        
        time.sleep(1)

if __name__ == "__main__":
    run_simulation()