from backend.services.gpa import compute_gpa, what_if_final

def test_empty():
    assert compute_gpa([])==0

def test_single():
    assert compute_gpa([{"weight":100,"score":85,"max_score":100}])==3.0

def test_weights_normalize():
    # 60+60=120 should normalize same as 50+50
    assert compute_gpa([{"weight":60,"score":90,"max_score":100},{"weight":60,"score":90,"max_score":100}])==4.0

def test_zero_max():
    assert compute_gpa([{"weight":100,"score":0,"max_score":0}])==0

def test_what_if():
    cur=[{"weight":80,"score":70,"max_score":100}]
    assert what_if_final(cur,20,3.0) is not None
