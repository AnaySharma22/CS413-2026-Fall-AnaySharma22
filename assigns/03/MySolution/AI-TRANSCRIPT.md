# AI transcript

AI system: Cursor, used while writing Assignment 3.

## Initial prompt

Sync the class repository, then complete Assignment 3: turn `LAMBDA-UI-informal-requirements.md` into a requirements specification under `assigns/03/MySolution/`.

## Follow-up constraints taken from Assign03.md

- Stakeholders, scope, and a boundary between the environment and the compiler.
- Five to eight clarification questions, each with why it matters.
- Do not invent stakeholder answers. Use assumptions or mark items unresolved.
- About 12–20 functional requirements and 3–5 quality requirements, each with an id.
- Acceptance checks for at least six requirements, including two failure cases.
- A traceability table and at least three review issues with how they were fixed.
- No implementation.

## What the assistant produced

A single `REQUIREMENTS.md` with those sections, plus this transcript.

## Review before submission

I checked the draft against the brief rather than treating the generated wording as final:

- Sharing with the class stays out of version 1 because the brief says it can wait. Local persistence stays in, because refresh loss is called out as a problem.
- “Fast” and “easy” were removed unless a check was stated, and those numbers are labeled as proposals (A8, A9).
- Check and Run are separate requirements so a compile-only request cannot be read as an execution result.
- Sample mode must label every result, matching the brief’s warning not to confuse samples with compilation.
- Q3’s automatic timeout is left unresolved; only user cancel is required.

No source code was added for this assignment.
