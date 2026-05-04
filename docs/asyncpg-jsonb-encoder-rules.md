# asyncpg JSONB codec encoder rules

Repo policy and the empirical rule behind it. Read before writing any new
DB call that binds a parameter to a JSONB column.

## Summary

`api/database.py` registers a `set_type_codec` for `pg_catalog.jsonb` with
`encoder=json.dumps, decoder=json.loads, format='text'`. **The encoder fires
on every parameter bound to a JSONB column.** It does not matter whether the
SQL has an explicit `$N::jsonb` cast, whether it is INSERT or UPDATE or
UPSERT, single-column or multi-column, inside an explicit transaction or
not, after a `SELECT FOR UPDATE` or not. The encoder runs.

That means there is one — and only one — correct call shape:

> **Pass Python objects directly. Never pre-stringify with `json.dumps()`,
> `model_dump_json()`, or any other serializer when the parameter binds to
> a JSONB column.**

Pre-stringifying causes double-encoding: the codec calls `json.dumps()` on
the already-serialized text, Postgres parses one level of the cast, and
the column ends up storing a JSONB **string** (`jsonb_typeof = 'string'`)
instead of a JSONB **object** or **array**. Reads then come back as Python
`str`, breaking `dict(...)` and `len(...)` callers downstream. Three
production incidents in 24 hours (5.4.4 → 5.4.5 → 5.4.6) traced to this
exact pattern in different routes.

## The rule (verified empirically)

Test matrix run against PostgreSQL 16 with asyncpg 0.31.0, direct
connection, codec registered as in `api/database.py`. Payload is a
nested dict; payload-as-string is `json.dumps(payload)`.

| Variant                                     | Pass `dict`/`list` | Pass `str` (`json.dumps`) |
| ------------------------------------------- | ------------------ | ------------------------- |
| `INSERT (..., $N::jsonb)` single col        | `object` ✓         | `string` ✗                |
| `INSERT (..., $N)` single col, no cast      | `object` ✓         | `string` ✗                |
| `UPDATE SET col = $N::jsonb` single col     | `object` ✓         | `string` ✗                |
| `UPDATE SET col = $N` single col, no cast   | `object` ✓         | `string` ✗                |
| `UPDATE SET a = $1::jsonb, b = $2::jsonb`   | `object` ✓         | `string` ✗                |
| `INSERT ... ON CONFLICT DO UPDATE` (UPSERT) | `object` ✓         | `string` ✗                |
| Inside `async with conn.transaction():`     | `object` ✓         | `string` ✗                |
| After `SELECT ... FOR UPDATE` on same conn  | `object` ✓         | `string` ✗                |
| Array append `log = log || $1::jsonb`       | `array` ✓          | `array` ✓ (lucky) [1]     |

[1] The array-append case happens to round-trip whether you pass the list
or the JSON-stringified list, because `json.dumps(json.dumps(list))` is
itself a JSON-encoded string that Postgres tolerates as a JSONB value at
the `||` operator's RHS for some inputs. Do not rely on this; pass the
list.

## Why the encoder fires unconditionally

asyncpg uses Postgres' Bind/Execute protocol. When a statement is prepared,
asyncpg learns the column type for each result column AND, where the type
of a parameter can be inferred, the parameter type. For a query like
`UPDATE game_states SET character = $1::jsonb`, asyncpg sees that the
target column is JSONB (regardless of the explicit cast) and applies the
codec encoder for `pg_catalog.jsonb` to `$1`. The encoder turns the value
into the text format Postgres expects. Postgres then parses that text into
JSONB.

`set_type_codec`'s docstring (asyncpg 0.31.0,
`asyncpg/connection.py:1262-1382`) is explicit:

> :param encoder: Callable accepting a Python object as a single argument
> and returning a value encoded according to *format*.

There is no "skip encoder if value is already a string" branch. The
parameter goes through the encoder if a codec matches the parameter type;
the parameter type is taken from the column type when binding to that
column, with or without `::jsonb`. The cast does not bypass encoding.

## Repo policy

1. **For any DB call that binds a parameter to a JSONB column, pass the
   Python object directly.** Use `dict`, `list`, primitives, or the result
   of `model.model_dump(mode="json")`. Do not pass `json.dumps(...)`,
   `model.model_dump_json()`, or any other pre-serialized form.

2. Keep `::jsonb` casts in SQL where they currently exist. They are
   cosmetic with the codec registered, but they make column type
   intent explicit and are no harm. Do not add new ones for new
   columns; do not bulk-remove existing ones either. **The cast is not
   load-bearing.**

3. Do not register additional encoders for JSONB or change the `format`
   argument on the codec. The codec is doing its job correctly. The bug
   class is in the calling code, not the codec.

4. Test fakes that intercept asyncpg calls should accept either Python
   objects (the production shape) or strings (legacy or third-party
   shape) defensively:
   ```python
   value = args[N] if isinstance(args[N], (dict, list)) else json.loads(args[N])
   ```

## Migration note

The 5.4.6 sweep (commit `29c408c`) eliminated every known
`json.dumps(...)`/`model.model_dump_json()` paired with a JSONB-bound
parameter across the repo. New code must follow this policy. Reviewers
should reject PRs that reintroduce the pattern.

## Worked examples

### Correct

```python
# Pass dict directly. Encoder runs once: json.dumps(dict) → JSON text
# → Postgres parses → jsonb_typeof = 'object'.
await conn.execute(
    "UPDATE game_states SET character = $1::jsonb WHERE session_id = $2",
    character_dict,
    session_id,
)
```

```python
# Pydantic model: dump as a JSON-serializable dict, not as a JSON string.
await conn.execute(
    "UPDATE game_states SET character = $1::jsonb WHERE session_id = $2",
    character_model.model_dump(mode="json"),
    session_id,
)
```

```python
# List for an array column. Pass list directly.
await conn.execute(
    "UPDATE game_states SET log = log || $1::jsonb WHERE session_id = $2",
    [entry.model_dump(exclude_none=True)],
    session_id,
)
```

### Incorrect

```python
# Encoder runs, double-encodes. Stored as jsonb_typeof = 'string'.
# Reads come back as Python str. Callers crash on dict(...).
await conn.execute(
    "UPDATE game_states SET character = $1::jsonb WHERE session_id = $2",
    json.dumps(character_dict),  # ← REMOVE
    session_id,
)
```

```python
# Same bug with a Pydantic helper.
await conn.execute(
    "UPDATE game_states SET character = $1::jsonb WHERE session_id = $2",
    character_model.model_dump_json(),  # ← REMOVE; use .model_dump(mode="json")
    session_id,
)
```

## Detection

Quick repo-wide check for the bug class:

```bash
grep -rn "json\.dumps\|model_dump_json" api/ --include="*.py" | grep -v __pycache__
```

Anything from this list that is bound to a parameter on a JSONB column is
a regression. The only legitimate uses are:

- `api/database.py` — the codec encoder definition itself.
- Deep-copy idiom `json.loads(json.dumps(obj))` (no DB binding).
- Hashing/logging of JSON content (no DB binding).

## Production sweep

To verify no double-encoded data exists in the database:

```sql
-- Per-table check; extend as new JSONB columns are added.
SELECT 'game_states.character' AS col, jsonb_typeof(character) AS t, COUNT(*) FROM game_states GROUP BY t
UNION ALL SELECT 'game_states.world',           jsonb_typeof(world),     COUNT(*) FROM game_states GROUP BY jsonb_typeof(world)
UNION ALL SELECT 'game_states.log',             jsonb_typeof(log),       COUNT(*) FROM game_states GROUP BY jsonb_typeof(log)
UNION ALL SELECT 'arcs.data',                   jsonb_typeof(data),      COUNT(*) FROM arcs        GROUP BY jsonb_typeof(data)
UNION ALL SELECT 'scene_records.scene_actions', jsonb_typeof(scene_actions),     COUNT(*) FROM scene_records GROUP BY jsonb_typeof(scene_actions)
UNION ALL SELECT 'scene_records.arc_progressed_ids', jsonb_typeof(arc_progressed_ids), COUNT(*) FROM scene_records GROUP BY jsonb_typeof(arc_progressed_ids)
UNION ALL SELECT 'scene_records.time_at_resolution', jsonb_typeof(time_at_resolution), COUNT(*) FROM scene_records WHERE time_at_resolution IS NOT NULL GROUP BY jsonb_typeof(time_at_resolution)
UNION ALL SELECT 'arc_transitions.locations_visited_at_transition', jsonb_typeof(locations_visited_at_transition), COUNT(*) FROM arc_transitions GROUP BY jsonb_typeof(locations_visited_at_transition)
UNION ALL SELECT 'locations.data', jsonb_typeof(data), COUNT(*) FROM locations GROUP BY jsonb_typeof(data)
ORDER BY 1, 2;
```

`'string'` rows for a column that should hold an object/array are
corrupted writes. Repair with:

```sql
UPDATE <table>
   SET <col> = (<col> #>> '{}')::jsonb
 WHERE jsonb_typeof(<col>) = 'string';
```

## Why this took three incidents to land

We hypothesized at first that `$N::jsonb` casts bypassed the encoder, and
that some asyncpg internal state determined which writes corrupted. The
matrix in the previous section disproves both: the cast does not bypass
the encoder, and the behavior is fully deterministic on the type of the
Python value passed. The reason corruption appeared inconsistent in
production was that the **last** write to a row determines what's stored;
clean dict-passing writes overwrote earlier string-passing corruption,
making `jsonb_typeof` checks at any single moment look clean even when
half the write paths were buggy. Only when a buggy write was the most
recent did corruption persist.

The lesson for similar future bugs: when the encoder/decoder pipeline
shapes the data, probe behavior in controlled isolation against the actual
library — don't reason from "looks clean in DB right now" to "no bug
exists in any write path."
