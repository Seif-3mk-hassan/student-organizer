"""Notifications — windows-toasts on Win, notifypy fallback, APScheduler hook."""
import platform
try:
    from windows_toasts import Toast, WindowsToaster
    _W_TOASTER = WindowsToaster("Student Organizer")
except: _W_TOASTER = None

def notify(title: str, body: str) -> bool:
    try:
        if platform.system() == "Windows" and _W_TOASTER:
            t = Toast(); t.text_fields = [title, body]
            _W_TOASTER.show_toast(t)
            return True
        # fallback: try notifypy/plyer — no-op if silent
        try:
            from notifypy import Notify
            n = Notify(); n.title = title; n.message = body; n.send()
            return True
        except: return False
    except Exception:
        return False

def schedule_checks():
    # APScheduler is wired in app.py as interval job; stub kept testable
    from ..bridge import api
    from ..database import SessionLocal
    from .. import models
    db = SessionLocal()
    try:
        soon = [r for r in db.query(models.Assignment).all() if not r.is_late and r.status=="todo"]
        for a in soon[:3]:
            notify("Due soon", a.title)
    finally: db.close()
