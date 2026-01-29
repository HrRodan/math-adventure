import gradio as gr
import json
import os
from backend.controller import GameController
from backend.database import get_all_sessions, delete_session

controller = GameController()

# CSS laden und erweitern
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
with open(css_path, "r") as f:
    custom_css = f.read() + """
    .celebration {
        animation: party 0.5s ease infinite alternate;
        font-size: 3rem !important;
        text-align: center;
    }
    @keyframes party {
        from { transform: scale(1); }
        to { transform: scale(1.2) rotate(5deg); }
    }
    .delete-btn { background-color: #ff7675 !important; font-size: 1rem !important; padding: 5px 10px !important; }
    """

# --- Hilfsfunktionen ---

def format_math_box(content, state="neutral", header="Deine Aufgabe"):
    css_class = "math-box"
    if state == "wrong": css_class += " feedback-wrong"
    if state == "correct": css_class += " feedback-correct"
    
    # Bei "correct" fügen wir ein bisschen Party-Spirit hinzu
    header_content = header
    if state == "correct":
        header_content = "✨ RICHTIG! ✨"
        
    return f'<div class="{css_class}"><div class="math-header">{header_content}</div><div class="math-content">{content}</div></div>'

def append_question_to_story(story, question):
    return f"{story}\n\n**❓ Rätsel:** {question}"

def refresh_sessions():
    sessions = get_all_sessions()
    choices = [s[1] for s in sessions]
    mapping = {s[1]: s[0] for s in sessions}
    return gr.update(choices=choices, value=None), mapping

def handle_delete(session_desc, session_mapping):
    if not session_desc: return refresh_sessions()
    s_id = session_mapping.get(session_desc)
    if s_id:
        delete_session(s_id)
    return refresh_sessions()

def start_new_game(theme, model_name):
    session_id, data, stars = controller.start_new_game(theme, model_name)
    story_text = f"**ABENTEUER START: {theme.upper()}**\n\n{append_question_to_story(data['story'], data['question'])}"
    chat_history = [{"role": "assistant", "content": story_text}]
    return (
        session_id, data['answer'], data['question'], chat_history, 
        format_math_box(data['question']), "", 
        gr.update(visible=False), gr.update(visible=True), theme, model_name,
        f"⭐ {stars}"
    )

def load_existing_game(session_desc, session_mapping):
    if not session_desc: return [None] * 11
    s_id = session_mapping[session_desc]
    theme, model_name, raw_history, last_data, stars = controller.load_game(s_id)
    
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
        gr.update(visible=False), gr.update(visible=True), theme, model_name,
        f"⭐ {stars}"
    )

def submit_answer(user_input, session_id, expected_answer, current_q_text, chat_history, theme, model_name):
    is_correct, new_data, stars = controller.submit_answer(session_id, user_input, expected_answer, model_name, theme)
    
    if not is_correct:
        html = format_math_box(current_q_text, state="wrong", header="Leider falsch - Probier es nochmal!")
        return session_id, expected_answer, current_q_text, chat_history, html, user_input, gr.update(), gr.skip()
    
    # Richtig gelöst!
    chat_history.append({"role": "user", "content": f"Antwort: {user_input}"})
    chat_history.append({"role": "assistant", "content": append_question_to_story(new_data['story'], new_data['question'])})
    
    new_q = new_data['question']
    html = format_math_box(new_q, state="correct", header="SUPER GEMACHT!") # Zeigt kurz "Super Gemacht"
    
    return session_id, new_data['answer'], new_q, chat_history, html, "", gr.update(), f"⭐ {stars}"

def reset_to_start():
    return gr.update(visible=True), gr.update(visible=False)

# --- UI Aufbau ---

with gr.Blocks(title="Mein Mathe-Abenteuer") as demo:
    session_id = gr.Textbox(visible=False)
    expected_answer = gr.Textbox(visible=False)
    current_q_text = gr.State(value="")
    session_mapping = gr.State(value={})
    current_theme = gr.State(value="")
    current_model = gr.State(value="")
    
    with gr.Row():
        gr.HTML("<h1>✨ Mein Mathe-Abenteuer ✨</h1>", scale=4)
        star_display = gr.Markdown("⭐ 0", elem_classes="star-counter")
    
    # Start-Bildschirm
    with gr.Row(variant="panel") as setup_row:
        with gr.Column():
            gr.Markdown("### 🆕 Neues Abenteuer")
            theme_input = gr.Textbox(label="Worum soll es gehen?", value="Drachenreiter", placeholder="z.B. Minecraft, Dschungel...")
            model_dropdown = gr.Dropdown(
                label="Erzähler", 
                choices=["gemini-2.0-flash", "gemini-3-flash-preview", "gpt-4o-mini", "openai/gpt-oss-120b"], 
                value="gemini-3-flash-preview"
            )
            start_btn = gr.Button("Abenteuer starten! 🚀", variant="primary")
        with gr.Column():
            gr.Markdown("### 📖 Deine Bücher")
            session_dropdown = gr.Dropdown(label="Wähle ein Buch aus", choices=[])
            with gr.Row():
                load_btn = gr.Button("Weiterlesen 📖", variant="secondary")
                delete_btn = gr.Button("Buch löschen 🗑️", variant="stop", elem_classes="delete-btn")
            
    # Spiel-Bildschirm
    with gr.Column(visible=False) as game_row:
        chatbot = gr.Chatbot(label="Dein Buch", height=550, buttons=[])
        
        with gr.Row():
            with gr.Column(scale=3): 
                math_question_display = gr.HTML() 
            with gr.Column(scale=2):
                answer_input = gr.Textbox(label="Deine Lösung:", placeholder="Schreib hier die Zahl...")
                submit_btn = gr.Button("Ist das richtig? ✨", variant="primary")
        
        new_book_btn = gr.Button("📔 Zurück zum Regal", variant="secondary")

    # Events
    demo.load(fn=refresh_sessions, outputs=[session_dropdown, session_mapping])
    
    start_btn.click(
        fn=start_new_game, 
        inputs=[theme_input, model_dropdown], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model, star_display],
        show_progress="minimal"
    )
    
    load_btn.click(
        fn=load_existing_game, 
        inputs=[session_dropdown, session_mapping],
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, setup_row, game_row, current_theme, current_model, star_display],
        show_progress="minimal"
    )
    
    delete_btn.click(
        fn=handle_delete,
        inputs=[session_dropdown, session_mapping],
        outputs=[session_dropdown, session_mapping]
    )
    
    submit_btn.click(
        fn=submit_answer, 
        inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display, star_display],
        show_progress="minimal"
    )
    
    answer_input.submit(
        fn=submit_answer, 
        inputs=[answer_input, session_id, expected_answer, current_q_text, chatbot, current_theme, current_model], 
        outputs=[session_id, expected_answer, current_q_text, chatbot, math_question_display, answer_input, math_question_display, star_display],
        show_progress="minimal"
    )

    new_book_btn.click(fn=reset_to_start, outputs=[setup_row, game_row])
    new_book_btn.click(fn=refresh_sessions, outputs=[session_dropdown, session_mapping])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=3000, css=custom_css, theme=gr.themes.Soft())