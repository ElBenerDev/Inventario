from datetime import datetime
from flask import session, request, redirect, url_for, flash
from functools import wraps
from typing import Optional

class SessionManager:
    @staticmethod
    def get_current_user_id() -> Optional[int]:
        return session.get('user_id')

    @staticmethod
    def get_current_username() -> Optional[str]:
        return session.get('username')

    @staticmethod
    def get_current_user_role() -> Optional[str]:
        return session.get('user_role')

    @staticmethod
    def set_user_session(user_id: int, username: str, role: str):
        session['user_id'] = user_id
        session['username'] = username
        session['user_role'] = role
        session['last_activity'] = datetime.now().timestamp()

    @staticmethod
    def clear_session():
        session.clear()

    @staticmethod
    def update_last_activity():
        session['last_activity'] = datetime.now().timestamp()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.get_current_user_id():
            flash('Por favor inicie sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        SessionManager.update_last_activity()
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not SessionManager.get_current_user_id():
                flash('Por favor inicie sesión para acceder a esta página', 'error')
                return redirect(url_for('login'))
            
            current_role = SessionManager.get_current_user_role()
            if current_role not in roles:
                flash('No tiene permisos suficientes para acceder a esta página', 'error')
                return redirect(url_for('index'))
            
            SessionManager.update_last_activity()
            return f(*args, **kwargs)
        return decorated_function
    return decorator