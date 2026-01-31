import gradio as gr
import json
import os
from typing import Tuple, List, Any
from backend.controller import GameController
from backend.database import get_all_sessions, delete_session
from backend.config import get_all_models

# Controller initialisieren
controller = GameController()

# CSS laden (Wird später in launch() übergeben)
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
with open(css_path, "r") as f:
    custom_css = f.read()

# --- Hilfsfunktionen für HTML-Formatierung ---

def format_math_box(content: str, state: str = "neutral", header: str = "Deine Aufgabe") -> str:
    """
    Erstellt das HTML für die Mathe-Aufgaben-Box.
    
    Args:
        content (str): Der Text der Aufgabe (z.B. "5 + 5 = ?").
        state (str): 'neutral', 'correct' oder 'wrong'. Beeinflusst CSS-Klassen.
        header (str): Die Überschrift der Box.
        
    Returns:
        str: HTML-String.
    """
    css_class = "math-box"
    if state == "wrong": css_class += " feedback-wrong"
    if state == "correct": css_class += " feedback-correct"
    
    header_content = header
    if state == "correct": header_content = "✨ RICHTIG! ✨"
    return f'<div class="{css_class}"><div class="math-header">{header_content}</div><div class="math-content">{content}</div></div>'

def append_question_to_story(story: str, question: str) -> str:
    """Formatiert Story und Frage für den Chatverlauf."""
    return f"{story}\n\n**❓ Rätsel:** {question}"

def refresh_sessions() -> Tuple[gr.Dropdown, dict]:
    """Lädt die Session-Liste aus der DB und aktualisiert das Dropdown."""
    sessions = get_all_sessions()
    choices = [s[1] for s in sessions]
    mapping = {s[1]: s[0] for s in sessions} # Name -> ID Mapping
    return gr.update(choices=choices, value=None), mapping

def handle_delete(session_desc: str, session_mapping: dict) -> Tuple[gr.Dropdown, dict]:
    """Callback für den Löschen-Button."""
    if not session_desc: return refresh_sessions()
    s_id = session_mapping.get(session_desc)
    if s_id: delete_session(s_id)
    return refresh_sessions()

# --- Game Flow Callbacks (Gradio Event Handler) ---

def start_new_game(theme: str, model_name: str) -> Tuple[Any, ...]:
    """Startet ein neues Spiel."""
    if not model_name: model_name = get_all_models()[0]
        
    session_id, data, arc = controller.start_new_game(theme, model_name)
    
    if not data:
        # Fehlerfall
        return (None, None, None, None, format_math_box("Fehler"), "", gr.update(), gr.update(), theme, model_name, "Fehler")

    story_text = f"**ABENTEUER START: {theme.upper()}**\n\n{append_question_to_story(data['story'], data['question'])}"
    chat_history = [{"role": "assistant", "content": story_text}]
    arc_text = f"**Geheimer Plan des Erzählers:**\n\n{arc}"
    
    return (
        session_id, data['answer'], data['question'], chat_history, 
        format_math_box(data['question']), "", 
        gr.update(visible=False), gr.update(visible=True), theme, model_name,
        arc_text
    )

def load_existing_game(session_desc: str, session_mapping: dict) -> Tuple[Any, ...]:
    """Lädt ein Spiel."""
    if not session_desc: return [None] * 11
    s_id = session_mapping[session_desc]
    theme, model_name, raw_history, last_data, arc = controller.load_game(s_id)
    
    # Verlauf für Chatbot aufbereiten
    ui_history = []
    for m in raw_history:
        role, content = m['role'], m['content']
        if role == 'assistant':
            try:
                d = json.loads(content)
                text = append_question_to_story(d['story'], d['question'])
                ui_history.append({"role": "assistant", "content": text})
            except:
                ui_history.append({"role": "assistant", "content": content})
        else:
            ui_history.append({"role": "user", "content": content})
            
    q_text = last_data.get('question', '...')
    arc_text = f"**Geheimer Plan des Erzählers:**\n\n{arc}"
    
    return (
        s_id, last_data['answer'], q_text, ui_history, 
        format_math_box(q_text), "", 
        gr.update(visible=False), gr.update(visible=True), theme, model_name,
        arc_text
    )

def submit_answer(user_input: str, session_id: str, expected_answer: str, current_q_text: str, chat_history: List[dict], theme: str, model_name: str) -> Tuple[Any, ...]:
    """Prüft die Antwort und holt den nächsten Zug."""
    # Konvertiere session_id zurück zu int
    try: s_id_int = int(session_id)
    except: return (None, None, None, None, None, None, gr.update())

    is_correct, new_data = controller.submit_answer(s_id_int, user_input, expected_answer, model_name, theme)
    
    if not is_correct:
        html = format_math_box(current_q_text, state="wrong", header="Leider falsch - Probier es nochmal!")
        return session_id, expected_answer, current_q_text, chat_history, html, user_input, gr.update()
    
    # Update UI History
    chat_history.append({"role": "user", "content": f"Antwort: {user_input}"})
    chat_history.append({"role": "assistant", "content": append_question_to_story(new_data['story'], new_data['question'])})
    
    new_q = new_data['question']
    html = format_math_box(new_q, state="correct", header="SUPER GEMACHT!")
    
    return session_id, new_data['answer'], new_q, chat_history, html, "", gr.update()

def reset_to_start() -> Tuple[gr.update, gr.update]:
    """Wechselt zurück zur Startansicht."""
    return gr.update(visible=True), gr.update(visible=False)

# --- UI Aufbau (Gradio Blocks) ---

with gr.Blocks(title="Mein Mathe-Abenteuer") as demo:
    # State Variablen (unsichtbar)
    session_id = gr.Textbox(visible=False); expected_answer = gr.Textbox(visible=False)
    current_q_text = gr.State(value="")
    session_mapping = gr.State(value={}); current_theme = gr.State(value=""); current_model = gr.State(value="")
    
    with gr.Row():
        gr.HTML("<h1>✨ Mein Mathe-Abenteuer ✨</h1>", scale=4)
    
    # Start-Bildschirm
    with gr.Row(variant="panel") as setup_row:
        with gr.Column():
            gr.Markdown("### 🆕 Neues Abenteuer")
            theme_input = gr.Textbox(label="Thema", value="Ritterburg")
            
            available_models = get_all_models()
            model_dropdown = gr.Dropdown(label="Erzähler", choices=available_models, value=available_models[0] if available_models else None, interactive=True)
            start_btn = gr.Button("Los geht's! 🚀", variant="primary")
        with gr.Column():
            gr.Markdown("### 📖 Weiterspielen")
            session_dropdown = gr.Dropdown(label="Deine Bücher", choices=[])
            with gr.Row():
                load_btn = gr.Button("Buch aufschlagen 📖", variant="secondary")
                delete_btn = gr.Button("Löschen 🗑️", variant="stop", elem_classes="delete-btn")
            
    # Spiel-Bildschirm
    with gr.Column(visible=False) as game_row:
        chatbot = gr.Chatbot(label="Deine Geschichte", height=500, buttons=[])
        
        with gr.Accordion("🕵️ Blick hinter die Kulissen (Story-Plan)", open=False):
            arc_display = gr.Markdown("Noch kein Plan...")
        
        with gr.Row():
            with gr.Column(scale=3): math_question_display = gr.HTML() 
            with gr.Column(scale=2):
                answer_input = gr.Textbox(label="Lösung:", placeholder="Zahl...")
                submit_btn = gr.Button("Prüfen ✨", variant="primary")
        
        new_book_btn = gr.Button("📔 Zurück zum Regal", variant="secondary")

    # Events verdrahten
    demo.load(fn=refresh_sessions, outputs=[session_dropdown, session_mapping])
    
    start_btn.click(
        fn=start_new_game, 
        inputs=[theme_input, model_dropdown], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model, arc_display],
        show_progress="minimal"
    )
    
    load_btn.click(
        fn=load_existing_game, 
        inputs=[session_dropdown, session_mapping], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model, arc_display],
        show_progress="minimal"
    )
    
    delete_btn.click(fn=handle_delete, inputs=[session_dropdown, session_mapping], outputs=[session_dropdown, session_mapping])
    
    submit_btn.click(
        fn=submit_answer, 
        inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display],
        show_progress="minimal"
    )
    
    answer_input.submit(
        fn=submit_answer, 
        inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display],
        show_progress="minimal"
    )

    new_book_btn.click(fn=reset_to_start, outputs=[setup_row, game_row])
    new_book_btn.click(fn=refresh_sessions, outputs=[session_dropdown, session_mapping])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=3000, css=custom_css, theme=gr.themes.Soft())