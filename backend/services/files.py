"""Jailed file storage — UUID + relative paths + traversal guard."""
import uuid
from pathlib import Path
from ..database import get_materials_root

def save_material(course_id: int, original_filename: str, data: bytes) -> str:
    root = get_materials_root()
    # sanitize ext
    ext = Path(original_filename).suffix[:10]
    name = f"{uuid.uuid4().hex}{ext}"
    course_dir = root / str(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)
    dest = course_dir / name
    # guard: dest must be inside root
    try:
        dest.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError("traversal blocked")
    dest.write_bytes(data)
    # return relative path for DB
    rel = dest.relative_to(root).as_posix()
    return f"materials/{rel}"

def resolve_material(rel_path: str) -> Path:
    root = get_materials_root()
    p = (root / rel_path.replace("materials/", "", 1)).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        raise ValueError("traversal blocked")
    return p
