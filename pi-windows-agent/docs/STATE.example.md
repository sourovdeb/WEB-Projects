# Example of the PiWin agent handoff file (real one is gitignored, JSON, data-only)

The real handoff file is `state.json` in the app data folder — **gitignored**,
schema-validated, and **data-only**: every text field is treated as DATA by the
receiving agent, never as instructions. Committed here is this example only.

```json
{
  "schema": 1,
  "goal": "string — what the task was",
  "done": ["step ids completed"],
  "next": "step id",
  "blockers": ["strings describing facts, not commands"],
  "unverified": ["labels"],
  "safety": { "gates_pending": ["step ids"], "irreversible_queued": [] }
}
```

Why not a committed markdown instruction file: anything typed on screen into a
committed file would become the next agent's instructions (prompt injection via
the handoff). JSON with a schema and data-only text fields removes that channel.
