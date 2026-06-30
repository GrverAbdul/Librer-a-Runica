# wsgi.py
# punto de entrada para servidores wsgi en produccion
# esto para render
from app.app import create_app

app = create_app()