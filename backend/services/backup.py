"""Snapshot backup via SQLite backup API — consistent even while WAL active."""
import sqlite3, zipfile, io
from pathlib import Path
from ..database import get_db_path

def create_snapshot_zip() -> bytes:
    src = get_db_path()
    if not src.exists():
        raise FileNotFoundError("no db yet")
    # use sqlite backup API to temp
    import tempfile, os
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        s = sqlite3.connect(str(src))
        d = sqlite3.connect(tmp)
        s.backup(d)
        s.close(); d.close()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, arcname="app.db")
            # also include materials listing (not blobs, just manifest)
        return buf.getvalue()
    finally:
        try: Path(tmp).unlink() 
        except: pass
