# Google Cloud TTS PR Audit (Production Readiness)

Date: 2026-04-01

## Scope
Static audit of Google Cloud TTS integration in:
- `app/tts/engine.py`
- `app/telegram/handlers.py`
- `app/config/settings.py`
- `app/telegram/bot.py`
- config/dependency/test files impacting voice runtime

## Key findings summary
- Integration works for happy-path but has several production blockers: no client reuse, no explicit API timeout/deadline, fragile enum parsing, outdated `.env.example`, and no ADC/operator documentation.
- The adapter boundary exists and Telegram fallback behavior is implemented.

## Critical issues
1. `TextToSpeechClient` is recreated on every synthesis request.
2. TTS request has no explicit deadline/timeout.
3. `.env.example` is stale and defaults `TTS_PROVIDER=piper`, which does not match runtime adapter support.
4. No validation for `TTS_AUDIO_ENCODING` and `TTS_VOICE_GENDER`; invalid values fail at runtime.

## High-priority improvements
- Lazy-initialize and reuse one GCP client per process.
- Add configurable timeout (e.g., `TTS_TIMEOUT_SECONDS`) and pass `timeout=` to `synthesize_speech`.
- Align `.env.example` to Google Cloud TTS + ADC workflow.
- Validate enum configs in `TTSSettings` with strict literals/enums.
- Add unit tests that assert one client instance reused across multiple calls and timeout is passed.
