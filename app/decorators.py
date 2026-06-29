# app/decorators.py
# decoradores personalizados para control de acceso con multiples roles

from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    """decorador que verifica que el usuario tenga uno de los roles indicados."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # usuario debe estar autenticado y tener uno de los roles permitidos
            if not current_user.is_authenticated or current_user.rol.nombre not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """caso particular: solo permite el rol 'administrador'."""
    return role_required('administrador')(f)