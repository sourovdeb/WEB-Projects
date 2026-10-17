# Jev (TypeSafe) integration — verification & cross-reference layer

## What Jev is (and is not)

Jev is a **decision model**, not a chat model (typesafe.ai docs, via search — site
blocked direct fetch; Pi docs VERIFIED-LIVE):

- Input: a `state` (JSON or text) + one or more typed `questions`
  (`choice`, `score`, `bool`).
- Output: typed answers with **calibrated probabilities and confidence** — no prose,
  no generation, no hallucination of format.
- Fast (~100–500 ms) and cheap; answers consumed directly by code.

So in PiWin: **Jev verifies and flags; a chat AI (Vibe or any added model)
suggests solutions where Jev flags a problem.** Jev never writes the fixes.

## Where it plugs in (four integration points)

### 1. Ambiguity check (before planning) — enforces the no-decision rule

Pi sends the operator's form input as `state` and asks Jev:

```
question: is_ambiguous (bool)
  true:  "The task leaves an action, target, or parameter unspecified"
  false: "Every step can be executed literally as specified"
```

If `probability(true) > 0.5` → the UI shows the single clarifying question form.
Pi is *never* allowed to resolve the ambiguity itself.

### 2. Plan conformance check (before each approval)

The step plan Pi produced is sent as `state`; for each step Jev answers:

```
question: matches_request (bool)
  true:  "This step is explicitly requested or a mechanical necessity of the request"
  false: "This step goes beyond or contradicts the request"
```

Any step below threshold is highlighted red in the UI checklist with the
probability shown — the operator decides, not the model.

### 3. Irreversible-action confirmation aid

For steps matching the irreversible keyword list, Jev scores:

```
question: risk (score)
  criteria: ["no side effects", "changes local files", "affects external services",
             "public/one-way action"]
```

The UI uses the score to size the confirmation dialog (from a simple confirm up
to showing a dry-run preview first).

### 4. Post-task cross-reference (operator-enableable option)

A checkbox in the task form: **"Cross-check result with another AI when done."**

- On task completion, PiWin assembles a run log (request, plan, each step's
  JSON result, screenshots) as `state`.
- Jev answers `bool`: "The run log shows every requested step completed
  successfully and nothing else was done."
- If flagged (or confidence low) and a second AI is configured, the run log is
  handed to that AI (e.g., Mistral Vibe via the shared STATE file / a second Pi
  model entry) which **suggests solutions** — shown in the UI as a plain-language
  report card with Fix suggestions. The operator clicks to accept any fix.

This is the Mistral Vibe + Pi + Jev triangle: Pi executes, Jev verifies,
Vibe (or any added model) proposes fixes.

## How it's wired technically (Pi-native, VERIFIED-LIVE)

Pi has TypeSafe Jev built in as a classifier model — no custom provider needed:

1. `defaultTools: ["+codemode"]` in `~/.pi/agent/settings.json` enables codemode.
2. `TYPESAFE_API_KEY` env var (or OpenRouter's `typesafe/jev-latest` with
   `OPENROUTER_API_KEY`) provides credentials.
3. PiWin's verification extension runs codemode scripts:

```js
const jev = await models.getModelOfType("classifier", "typesafe", "jev-latest");
const result = await models.classify(jev, {
  state: { task: taskFormJson, plan: stepPlan },
  questions: {
    matches_request: {
      type: "bool",
      instructions: "Does every step in the plan execute the task literally?",
      criteria: { true: "Yes, literal only", false: "Something goes beyond the request" },
    },
  },
});
return result.answers;
```

The PiWin UI backend (which drives Pi over RPC mode) triggers these checks and
renders the answers. Extensions can also call
`ctx.modelRegistry.classify()` directly, bypassing codemode.

## Caveats (documented, not hidden)

- Jev's output is a schema guarantee, not a truth guarantee — it can pick the
  wrong category. Thresholds default conservative (flag at ≥0.5) and every
  flagged item goes to the human, never auto-blocked or auto-fixed.
- Jev treats state as data; adversarial text can steer it (per TypeSafe's own
  notes). Irreversible gates therefore never depend on Jev alone — the human
  confirm stays mandatory.
- TypeSafe direct signups have been pause/limited at times; OpenRouter
  (`typesafe/jev-1.13`) is the fallback credential path.
