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

html = """
<!doctype html>
<meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<link rel=stylesheet href="frontend/css/tokens.css">
<link rel=stylesheet href="frontend/css/app.css">
<div id=app>
  <nav id=sidebar></nav>
  <main id=main></main>
</div>
<div id=palette hidden></div>
<script type=module src="frontend/js/app.js"></script>
"""

class Bridge:
    pass

# expose api methods to JS via pywebview api object
# webview expects an object instance; we delegate to api
def create_window():
    b = api  # direct
    w = webview.create_window("Student Organizer", html=html, js_api=b, width=1120, height=720, min_size=(1024,640))
    webview.start(debug=True)

if __name__ == "__main__":
    create_window()
