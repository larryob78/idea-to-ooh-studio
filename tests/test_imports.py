def test_analysis_import_smoke() -> None:
    import producer_amplifier.analysis as analysis

    assert hasattr(analysis, "scene_complexity_score")
    assert hasattr(analysis, "hidden_cost_flags")
    assert hasattr(analysis, "AssumptionsRepository")
    assert hasattr(analysis, "SnapshotsRepository")
    assert hasattr(analysis, "compare_snapshots")
