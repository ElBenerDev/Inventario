from functools import wraps
from flask import session, redirect, url_for, flash, request
from models import Usuario

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Por favor inicie sesión para acceder a esta página', 'error')
                return redirect(url_for('login', next=request.url))
            
            current_user = next((u for u in usuarios if u.id == session['user_id']), None)
            if not current_user or current_user.role not in roles:
                flash('No tiene permisos para acceder a esta página', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    if 'user_id' in session:
        return next((u for u in usuarios if u.id == session['user_id']), None)
    return None

# Lista temporal de usuarios (reemplazar por base de datos)
usuarios = [
    Usuario.create(
        username="admin",
        email="admin@ejemplo.com",
        password="admin123",
        role="admin"
    )
]
usuarios[0].id = 1