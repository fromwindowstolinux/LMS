from fastapi import Cookie

def get_current_user(session_id: str = Cookie(None)):
    if session_id == "logged_in":
        return True
    return False
