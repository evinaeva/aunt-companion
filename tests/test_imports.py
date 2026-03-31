def test_phase1_modules_importable():
    import app.main
    import app.config
    import app.db
    import app.telegram
    import app.domain
    import app.llm
    import app.stt
    import app.tts
    import app.jobs

    assert app.main is not None
