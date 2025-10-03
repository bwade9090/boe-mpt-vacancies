def test_import():
    import importlib

    assert importlib.import_module("boe_vac") is not None
