import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Ensure absolute path to data directory
# BASE_DIR = /home/devuser/gemini/math-adventure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'adventure.db')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

print(f"DATABASE PATH: {DB_PATH}", file=sys.stderr)

Base = declarative_base()

class GameSession(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    theme = Column(String)
    model = Column(String)
    stars = Column(Integer, default=0) # Die neue Spalte
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    role = Column(String) 
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("GameSession", back_populates="messages")

# Setup Engine
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Force recreation if schema mismatch (simple hack for dev)
# In production, use Alembic. Here, we just try to create.
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
    # Hier knallt es, wenn 'stars' fehlt
    sessions = db.query(GameSession).order_by(GameSession.created_at.desc()).all()
    result = [(s.id, f"Abenteuer {s.id}: {s.theme} ({s.created_at.strftime('%d.%m %H:%M')})") for s in sessions]
    db.close()
    return result

def get_session_by_id(session_id: int):
    db = SessionLocal()
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    theme, model = session.theme, session.model
    db.close()
    return theme, model