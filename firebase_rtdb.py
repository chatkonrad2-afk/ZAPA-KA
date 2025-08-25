# firebase_rtdb.py
import requests

DB_URL = "https://creditals-469401-default-rtdb.europe-west1.firebasedatabase.app"

def _url(path: str, id_token: str) -> str:
    return f"{DB_URL}/{path.strip('/')}.json?auth={id_token}"

def db_get(path: str, id_token: str):
    r = requests.get(_url(path, id_token), timeout=15)
    r.raise_for_status()
    return r.json()

def db_post(path: str, data: dict, id_token: str):
    r = requests.post(_url(path, id_token), json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def db_put(path: str, data: dict, id_token: str):
    r = requests.put(_url(path, id_token), json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def db_patch(path: str, data: dict, id_token: str):
    r = requests.patch(_url(path, id_token), json=data, timeout=15)
    r.raise_for_status()
    return r.json()
