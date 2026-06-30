#!/bin/bash
export FLASK_APP=app.app:create_app

echo "Aplicando migraciones..."
flask db upgrade

echo "Ejecutando seeds..."
flask seed
flask seed-books
flask seed-sig

echo "Iniciando aplicación..."
exec gunicorn wsgi:app