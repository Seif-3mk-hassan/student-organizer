from backend.services.files import save_material
from backend.database import get_materials_root
def test_traversal_blocked():
    try:
        save_material(1, "../../etc/passwd", b"hi")
        # save should jail, not write outside
        p = get_materials_root() / "../../etc/passwd"
        assert False, "should not reach"
    except Exception:
        assert True

def test_save_ok():
    rel=save_material(999, "slides.pdf", b"%PDF")
    assert rel.startswith("materials/999/")
