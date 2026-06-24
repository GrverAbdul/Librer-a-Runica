# app/decorators.py
# decoradores personalizados para control de acceso

from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """decorador que permite el acceso solo si el usuario tiene rol 'administrador'."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # verificar que el usuario este autenticado y tenga el rol adecuado
        if not current_user.is_authenticated or current_user.rol.nombre != "administrador":
            abort(403)  # prohibido
        return f(*args, **kwargs)
    return decorated_function