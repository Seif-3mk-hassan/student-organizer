"""Rotating file logger + Report Bug zip (CEO D3.6 deferred)."""
import logging, logging.handlers, io, zipfile, pathlib, platformdirs
from datetime import datetime

LOG_DIR = pathlib.Path(platformdirs.user_data_dir("student-organizer", "student-organizer")) / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

def get_logger(name="app"):
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=2)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        lg.addHandler(h); lg.setLevel(logging.INFO)
    return lg

def report_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if LOG_FILE.exists():
            z.write(LOG_FILE, arcname="app.log")
        # redact PII: no grades dump
        z.writestr("info.txt", f"generated {datetime.utcnow().isoformat()} platform {__import__('platform').system()}")
    return buf.getvalue()
