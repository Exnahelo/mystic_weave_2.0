"""Shared SQL templates for the /state save and /state delta endpoints.

Both endpoints UPSERT a session's game_states row and conditionally append a
log entry. The two SQL bodies are otherwise textually identical, so they live
here to prevent drift between the two routes.

Out of scope: companion.py and session.py write rows with structurally
different SQL (always-append vs. plain INSERT) and do not use these.
"""

# UPSERT that appends one log entry to the existing log array. Bound parameters:
# $1 session_id, $2 character_jsonb, $3 world_jsonb, $4 initial_log_jsonb,
# $5 entry_jsonb (used in the array-append on conflict).
GAME_STATE_UPSERT_WITH_LOG_APPEND = """
    INSERT INTO game_states (session_id, character, world, log, updated_at)
    VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
    ON CONFLICT (session_id) DO UPDATE
      SET character   = EXCLUDED.character,
          world       = EXCLUDED.world,
          log         = game_states.log || $5::jsonb,
          updated_at  = now()
    RETURNING session_id, character, world, log, updated_at
    """

# UPSERT that preserves the existing log unchanged. Bound parameters:
# $1 session_id, $2 character_jsonb, $3 world_jsonb, $4 initial_log_jsonb.
GAME_STATE_UPSERT_PRESERVE_LOG = """
    INSERT INTO game_states (session_id, character, world, log, updated_at)
    VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
    ON CONFLICT (session_id) DO UPDATE
      SET character   = EXCLUDED.character,
          world       = EXCLUDED.world,
          log         = game_states.log,
          updated_at  = now()
    RETURNING session_id, character, world, log, updated_at
    """
