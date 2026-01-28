import gradio as gr
import json
import os
from backend.controller import GameController
from backend.database import get_all_sessions

controller = GameController()

# CSS aus Datei laden
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
with open(css_path, "r") as f:
    custom_css = f.read()

# --- Hilfsfunktionen für UI-Elemente ---

def format_math_box(content, state="neutral", header="Deine Aufgabe"):
    """Erstellt das HTML für die interaktive Mathe-Box."""
    css_class = "math-box"
    if state == "wrong": css_class += " feedback-wrong"
    if state == "correct": css_class += " feedback-correct"
    return f'<div class="{css_class}"><div class="math-header">{header}</div><div class="math-content">{content}</div></div>'

def append_question_to_story(story, question):
    """Integriert die Frage lesbar in den Chat-Verlauf."""
    return f"{story}\n\n**❓ Rätsel:** {question}"

# --- Event Handler ---

def refresh_sessions():
    sessions = get_all_sessions()
    choices = [s[1] for s in sessions]
    mapping = {s[1]: s[0] for s in sessions}
    return gr.update(choices=choices), mapping

def start_new_game(theme, model_name):
    session_id, data = controller.start_new_game(theme, model_name)
    
    story_with_q = append_question_to_story(data['story'], data['question'])
    story_intro = f"**ABENTEUER START: {theme.upper()}**\n\n{story_with_q}"
    
    chat_history = [{"role": "assistant", "content": story_intro}]
    q_text = data['question']
    
    return (
        session_id, data['answer'], q_text, chat_history, 
        format_math_box(q_text), "", 
        gr.update(visible=False), gr.update(visible=True), theme, model_name
    )

def load_existing_game(session_desc, session_mapping):
    if not session_desc: return [None] * 10
    s_id = session_mapping[session_desc]
    theme, model_name, raw_history, last_data = controller.load_game(s_id)
    
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
    return (
        s_id, last_data['answer'], q_text, ui_history, 
        format_math_box(q_text), "", 
        gr.update(visible=False), gr.update(visible=True), theme, model_name
    )

def submit_answer(user_input, session_id, expected_answer, current_q_text, chat_history, theme, model_name):
    is_correct, new_data = controller.submit_answer(session_id, user_input, expected_answer, model_name, theme)
    
    if not is_correct:
        html = format_math_box(current_q_text, state="wrong", header="Leider falsch - Probier es nochmal!")
        return session_id, expected_answer, current_q_text, chat_history, html, user_input, gr.update()
    
    chat_history.append({"role": "user", "content": f"Antwort: {user_input}"})
    story_with_q = append_question_to_story(new_data['story'], new_data['question'])
    chat_history.append({"role": "assistant", "content": story_with_q})
    
    new_q = new_data['question']
    html = format_math_box(new_q, state="neutral", header="Nächste Aufgabe")
    
    return session_id, new_data['answer'], new_q, chat_history, html, "", gr.update()

# --- UI Aufbau ---

with gr.Blocks(title="Mein Mathe-Abenteuer", css=custom_css, theme=None) as demo:
    # State-Speicher (unsichtbar)
    session_id = gr.Textbox(visible=False)
    expected_answer = gr.Textbox(visible=False)
    current_q_text = gr.State(value="")
    session_mapping = gr.State(value={})
    current_theme = gr.State(value="")
    current_model = gr.State(value="")
    
    gr.HTML("<h1>✨ Mein Mathe-Abenteuer ✨</h1>")
    
    # Start-Bildschirm
    with gr.Row(variant="panel") as setup_row:
        with gr.Column():
            gr.Markdown("### 🆕 Neues Abenteuer")
            theme_input = gr.Textbox(label="Thema", value="Ritterburg")
            model_dropdown = gr.Dropdown(
                label="Erzähler", 
                choices=["gemini-2.0-flash", "gemini-3-flash-preview", "openai/gpt-oss-120b"], 
                value="gemini-2.0-flash"
            )
            start_btn = gr.Button("Los geht's! 🚀", variant="primary")
        with gr.Column():
            gr.Markdown("### 📖 Weiterspielen")
            session_dropdown = gr.Dropdown(label="Deine Bücher", choices=[])
            load_btn = gr.Button("Buch aufschlagen 📖", variant="secondary")
            
    # Spiel-Bildschirm (Initial versteckt)
    chatbot = gr.Chatbot(label="Deine Geschichte", height=550) # CSS blendet Buttons aus
    
    with gr.Row(visible=False) as game_row:
        with gr.Column(scale=1): 
            math_question_display = gr.HTML() 
        with gr.Column(scale=1):
            answer_input = gr.Textbox(label="Lösung:", placeholder="Zahl...", show_label=True)
            submit_btn = gr.Button("Prüfen ✨", variant="primary")
            
    # Event-Verknüpfungen
    demo.load(fn=refresh_sessions, outputs=[session_dropdown, session_mapping])
    
    start_btn.click(fn=start_new_game, inputs=[theme_input, model_dropdown], outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model])
    load_btn.click(fn=load_existing_game, inputs=[session_dropdown, session_mapping], outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model])
    
    submit_btn.click(fn=submit_answer, inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display])
    answer_input.submit(fn=submit_answer, inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=3000)
