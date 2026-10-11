from app.anomaly import classify_threshold, detect_spike, evaluate_reading


def test_missing_value_is_critical_anomaly():
    result = classify_threshold("PT08_S1", None, True)
    assert result["is_anomaly"] is True
    assert result["severity"] == "critical"
    assert "missing_value_sentinel" in result["reasons"]


def test_real_first_pt08_s1_is_not_a_threshold_violation():
    # 1360 is between min 647 and p95 1508 in the full UCI file.
    result = classify_threshold("PT08_S1", 1360.0, False)
    assert result["is_anomaly"] is False
    assert result["severity"] == "ok"


def test_p99_threshold_from_dataset():
    result = classify_threshold("CO_GT", 6.8, False)
    assert result["is_anomaly"] is True
    assert result["severity"] == "critical"


def test_spike_detection():
    assert detect_spike(100.0, 160.0) is True
    assert detect_spike(100.0, 110.0) is False


def test_evaluate_combines_reasons():
    result = evaluate_reading("CO_GT", 7.0, False, previous_value=1.0)
    assert "above_critical_high" in result["reasons"]
    assert "sudden_spike" in result["reasons"]
