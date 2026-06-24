# app/config.py
# configuracion central de la aplicacion flask

import os

class Config:
    # clave secreta para sesiones y tokens
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-por-defecto')

    # uri de la base de datos (sqlite para desarrollo, postgresql en produccion)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///libreria_runica.db')

    # desactiva el seguimiento de modificaciones para ahorrar recursos
    SQLALCHEMY_TRACK_MODIFICATIONS = False