import sys
import os
import re
import time

# Add root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.controller import GameController

def solve_math_problem(question_text):
    """
    Simulates a user solving the math problem.
    Handles '5 + 3 = ?' and '5 + ? = 8'
    """
    # Remove non-math chars
    clean = question_text.replace("?", "x").replace("=", "==")
    # Simple regex to find numbers
    nums = [int(n) for n in re.findall(r'\d+', question_text)]
    
    if len(nums) < 2:
        return 0 # Fallback
        
    if "+" in question_text:
        if question_text.strip().endswith("?"): # 5+3=?
            return nums[0] + nums[1]
        else: # 5+?=8 -> 8-5
            return max(nums) - min(nums)
    elif "-" in question_text:
        if question_text.strip().endswith("?"): # 5-3=?
            return nums[0] - nums[1]
        else: # 8-?=5 -> 8-5
            return max(nums) - min(nums)
    
    return nums[0] + nums[1] # Default fallback

def run_simulation():
    print("🤖 Starte autonome Agenten-Simulation...")
    controller = GameController()
    theme = "Cyberpunk Eichhörnchen"
    model = "gemini/gemini-2.0-flash" # Schnelles Modell für den Test
    
    # Start
    print(f"--- RUNDE 1 ---")
    session_id, data = controller.start_new_game(theme, model)
    expected = data['answer']
    print(f"Geschichte: {data['story']}")
    print(f"Aufgabe: {data['question']} (Erwartet: {expected})")
    
    for i in range(2, 21): # Bis zu 20 Runden
        print(f"\n--- RUNDE {i} ---")
        
        # Simuliere Benutzereingabe
        user_answer = expected 
        
        print(f"Benutzer sendet: {user_answer}")
        
        success, new_data = controller.submit_answer(session_id, user_answer, expected, model, theme)
        
        if not success:
            print("❌ Simulation fehlgeschlagen: Antwort abgelehnt.")
            break
            
        expected = new_data['answer']
        print(f"Geschichte: {new_data['story']}")
        print(f"Aufgabe: {new_data['question']} (Erwartet: {expected})")
        
        # Kurze Pause für die API
        time.sleep(1)

if __name__ == "__main__":
    run_simulation()
