# -*- coding: utf-8 -*-
# Prosty wrapper REST dla Identity Platform / Firebase Auth
# Email/Hasło: signUp + signInWithPassword + lookup + refresh

import requests

API_KEY = "AIzaSyCNWd9Ttl-RK1z5Y1bNLiIj1IM90shm5tY"  # z Twojej wiadomości
AUTH_DOMAIN = "creditals-469401.firebaseapp.com"     # nie jest potrzebny dla REST, ale zostawiamy

BASE = "https://identitytoolkit.googleapis.com/v1"


class AuthError(Exception):
    pass


def _post_json(url: str, payload: dict) -> dict:
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code >= 400:
        try:
            err = r.json()["error"]["message"]
        except Exception:
            err = r.text
        raise AuthError(err)
    return r.json()


def sign_up_email_password(email: str, password: str) -> dict:
    """Utwórz konto e-mail/hasło."""
    url = f"{BASE}/accounts:signUp?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return _post_json(url, payload)


def sign_in_email_password(email: str, password: str) -> dict:
    """Zaloguj e-mail/hasło."""
    url = f"{BASE}/accounts:signInWithPassword?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return _post_json(url, payload)


def lookup_user(id_token: str) -> dict:
    """Pobierz dane profilu użytkownika po idToken."""
    url = f"{BASE}/accounts:lookup?key={API_KEY}"
    payload = {"idToken": id_token}
    return _post_json(url, payload)


def refresh_id_token(refresh_token: str) -> dict:
    """Odśwież token (zwraca nowy id_token i refresh_token)."""
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    r = requests.post(url, data=data, timeout=15)
    if r.status_code >= 400:
        try:
            err = r.json()["error"]["message"]
        except Exception:
            err = r.text
        raise AuthError(err)
    return r.json()
