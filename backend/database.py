import os
from datetime import datetime
from typing import Generator, List, Tuple
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

# Projekt-Pfade definieren
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'adventure.db')

# Sicherstellen, dass das Datenverzeichnis existiert
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

Base = declarative_base()

class GameSession(Base):
    """
    Repräsentiert eine Spielsitzung (ein Buch/Abenteuer).
    """
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    theme = Column(String)
    model = Column(String)
    story_arc = Column(Text, default="") # Der interne "Rote Faden" der KI
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """
    Repräsentiert eine einzelne Nachricht (Seite/Chat-Bubble) innerhalb einer Session.
    """
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    role = Column(String) # 'user' oder 'assistant'
    content = Column(Text) # JSON-String bei Assistant, Klartext bei User
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("GameSession", back_populates="messages")

# SQLite Engine initialisieren
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Kontext-Manager für Datenbank-Sitzungen."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_session(theme: str, model: str) -> int:
    """Erstellt eine neue Spielsitzung und gibt deren ID zurück."""
    db = SessionLocal()
    session = GameSession(theme=theme, model=model)
    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()
    return session.id

def update_story_arc(session_id: int, arc: str) -> None:
    """Speichert den initialen Handlungsbogen für eine Session."""
    db = SessionLocal()
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if session:
        session.story_arc = arc
        db.commit()
    db.close()

def add_message(session_id: int, role: str, content: str) -> None:
    """Fügt eine Nachricht zum Verlauf hinzu."""
    db = SessionLocal()
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.close()

def get_history(session_id: int) -> List[dict]:
    """
    Lädt den gesamten Nachrichtenverlauf einer Session.
    
    Returns:
        List[dict]: Liste von Dictionaries mit 'role' und 'content'.
    """
    db = SessionLocal()
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.id).all()
    history = [{"role": m.role, "content": m.content} for m in msgs]
    db.close()
    return history

def get_all_sessions() -> List[Tuple[int, str]]:
    """
    Lädt eine Übersicht aller Sessions für das Dropdown-Menü.
    
    Returns:
        List[Tuple[int, str]]: Liste von (ID, Beschreibungs-String).
    """
    db = SessionLocal()
    sessions = db.query(GameSession).order_by(GameSession.created_at.desc()).all()
    result = [(s.id, f"Abenteuer {s.id}: {s.theme} ({s.created_at.strftime('%d.%m %H:%M')})") for s in sessions]
    db.close()
    return result

def get_session_details(session_id: int) -> Tuple[str, str, str]:
    """
    Lädt Metadaten einer Session.
    
    Returns:
        Tuple[str, str, str]: (Thema, Modell-Name, Story-Arc).
    """
    db = SessionLocal()
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    theme, model, arc = session.theme, session.model, session.story_arc
    db.close()
    return theme, model, arc

def delete_session(session_id: int) -> None:
    """Löscht eine Session und alle zugehörigen Nachrichten unwiderruflich."""
    db = SessionLocal()
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
    db.close()
