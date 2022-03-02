from sqlmodel import create_engine

engine = None

def get_db():
    global engine
    if engine is None:
        engine = create_engine('sqlite://')
    return engine
