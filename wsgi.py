# wsgi.py
# punto de entrada para servidores wsgi en produccion
from app.app import create_app

app = create_app()