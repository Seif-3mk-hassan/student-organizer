"""pywebview entry — JS Bridge, no HTTP server."""
import webview
from backend.database import Base, engine, get_db_path
from backend.bridge import api

# ensure tables + FTS exist before window
Base.metadata.create_all(bind=engine)
try:
    from backend.services.search import init_fts
    init_fts()
except: pass

class Bridge:
    pass

def create_window():
    from pathlib import Path
    b = api
    # use file URL so relative css/js resolve (html string cannot resolve frontend/ paths)
    entry = Path(__file__).parent / "frontend" / "index.html"
    url = entry.resolve().as_uri()
    w = webview.create_window("Student Organizer", url=url, js_api=b, width=1120, height=720, min_size=(1024,640))
    webview.start(debug=True)

if __name__ == "__main__":
    create_window()
