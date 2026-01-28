import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Ensure data directory exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'adventure.db')

Base = declarative_base()

class GameSession(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    theme = Column(String)
    model = Column(String)
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    role = Column(String) # 'user' or 'assistant' or 'system'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("GameSession", back_populates="messages")

# Setup Engine
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_session(theme: str, model: str):
    db = SessionLocal()
    session = GameSession(theme=theme, model=model)
    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()
    return session.id

def add_message(session_id: int, role: str, content: str):
    db = SessionLocal()
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.close()

def get_history(session_id: int):
    db = SessionLocal()
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.id).all()
    history = [{"role": m.role, "content": m.content} for m in msgs]
    db.close()
    return history

def get_all_sessions():
    db = SessionLocal()
    sessions = db.query(GameSession).order_by(GameSession.created_at.desc()).all()
    # Erstelle eine Liste von Strings für das Dropdown
    result = [(s.id, f"Abenteuer {s.id}: {s.theme} ({s.created_at.strftime('%d.%m %H:%M')})") for s in sessions]
    db.close()
    return result

def get_session_by_id(session_id: int):
    db = SessionLocal()
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    theme, model = session.theme, session.model
    db.close()
    return theme, model
