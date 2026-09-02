from backend.services.backup import create_snapshot_zip
from backend.database import Base, engine
from backend.bridge import api

def setup_module():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)

def test_backup_empty():
    z=create_snapshot_zip()
    assert len(z) > 100

def test_backup_after_data():
    api.createSemester({"name":"S","start_date":"2026-09-01","end_date":"2026-12-01"})
    z=create_snapshot_zip()
    assert len(z) > 100
