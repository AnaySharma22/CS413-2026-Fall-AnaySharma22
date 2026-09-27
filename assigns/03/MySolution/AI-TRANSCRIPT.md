# AI transcript

AI system: Cursor, in this repository.

I did not ask for a finished specification in one prompt. I went through the stakeholder brief with the assistant one piece at a time, then checked the class lecture notes before locking wording. Unrelated earlier work (Lab 1, Assignments 1 and 2) is left out.

## 1. Stakeholders and scope

**Me:** The brief lists students who write programs, students who change the compiler, and me using it in lecture. Is the compiler team a user or just a dependency?

**Assistant:** Treat them as a dependency. Their goal is a stable request/response shape. Building the compiler is a different project.

**Me:** I looked at `lectures/lecture-09-15/compiler_development.md`. That plan starts with a language spec and then lexer, parser, AST, and codegen. If I put parsing inside the web page, I am doing their project.

**Assistant:** Keep the page as a client. It sends source text and displays a status. It does not tokenize or evaluate.

**Me:** Sep 17 was the agile lecture. The brief already says they would rather agree a small version than discover a mismatch late. I want version 1 to drop accounts, a public site, and people editing the same buffer. Sharing a test collection with the class can wait; the brief says that out loud.

**What I kept:** four stakeholders, an explicit in/out list, and a paragraph that separates the environment from the compiler.

## 2. Clarification questions

**Me:** I need five to eight questions, and I should not invent answers from professor Hongwei.

**Assistant:** Each question should say why the answer changes a requirement, then either an assumption labeled as mine or an unresolved item.

**Me:** The biggest hole is syntax. The brief still talks about Python ASTs. I then read `lectures/lecture-09-22/README.md` and `lambda-concrete-syntax-requirements.md`. The README says there is still no parser. The syntax writeup says “Draft for discussion” and “not an approved language specification,” and section 3 defers editor integration. So I cannot write “the page accepts `lam` / `fix` / `let`” as if professor Hongwei signed off.

**Assistant:** Send the buffer as text. Say the compiler owns the notation. Until a parser exists, only the sample backend is real, and label it. Candidate spellings from Sep 22 can appear as sample example text, not as a frozen grammar.

**Me:** Storage is the next hole. No accounts, but refresh must not wipe examples. I am assuming browser-profile storage plus import/export, and I will mark that as my assumption.

**Me:** Timeout versus cancel. The brief only says I need a way to stop a run that might not finish. I am not going to invent a 5-second limit. Cancel is required. Automatic timeout stays unresolved.

**Me:** Tests. Integer, Boolean, or “the compiler rejects this.” I do not want version 1 to fail a test because the wording of an error changed. Exact diagnostic text stays out.

**Me:** Check versus Run should be two actions. Browsers: I’ll propose current Chrome, Firefox, Edge, and Safari and admit that two tabs can clobber the same store. Sample mode has to be labeled on every result, which the brief already asks for.

**What I kept:** Q1–Q7, assumptions A1–A7, and U1 left open.

## 3. Functional requirements

**Me:** I want about 12–20 testable requirements, not a restatement of every sentence with “shall.” Priorities should separate must, should, and wait.

**Assistant:** Suggested split: open and edit, examples that do not overwrite the original, save, Check, Run, distinct outcome labels, source location, environment failure, cancel while the page stays usable, result tied to the text that was sent, optional AST inspector, named tests, run-all that continues after a failure, persistence, sample versus real backend, export as a should.

**Me:** On locations, ERR-02 in the Sep 22 syntax draft asks for a one-based line and column on source errors, and ERR-04 says locations on runtime failures are deferred. So FR-09 should require a mark only when the compiler actually sends a line and column, and not for runtime errors.

**Me:** ERR-01 says lexical and syntactic failures stay distinct from runtime failures. If the compiler splits those, the page should not mash them into one red box. That became part of FR-08.

**Me:** The inspector should stay closed by default. The syntax notes defer editor integration, so the page must not grow its own parser. FR-13 is a should, not a must.

**What I kept:** FR-01 through FR-18, with FR-13 and FR-18 as should.

## 4. Quality requirements

**Me:** “Easy,” “fast,” and “promptly” are in the brief and they are not testable. I don’t want to leave them as adjectives.

**Assistant:** Keyboard paths for the main actions are already in the brief, so that can be a must without a made-up number. Color-only messages too. For speed, split UI actions from compiler time, and label any millisecond target as a proposal. Same for a setup-time target.

**Me:** I’ll use 200 ms for non-compiler actions and 15 minutes to open the page and run one example, both marked as my proposals (A8, A9). Compiler time is excluded. Persistence after reload is a real check, so that stays a must without a fake metric.

**What I kept:** QR-01 through QR-05.

## 5. Acceptance checks

**Me:** I need at least six checks, including two failures, written as future tests: start state, action, observable result. Not a test log from a program we didn’t build.

**Assistant:** Drafted checks for the example copy, a run that returns 6, a line/column mark, compiler-down, cancel during a nonterminating run, a result that goes stale if I edit mid-run, one bad test in a set of three, and reload.

**Me:** AC-4, AC-5, AC-6, and AC-7 are the failure or exceptional ones. I dropped a check that required the factorial source to parse, because that would pretend the Sep 22 grammar is approved. The factorial name can stay as a built-in example title.

**What I kept:** AC-1 through AC-8.

## 6. Traceability and review

**Me:** Every ID should point at a brief passage, a lecture note, or an assumption. Lecture notes are context. They are not “professor Hongwei answered Q1.”

**Assistant:** Mapped FR-01–FR-18 and QR-01–QR-05. FR-08 and FR-09 cite ERR-01, ERR-02, and ERR-04. FR-13 cites the deferred editor integration.

**Me:** Review of my own draft:

1. “Easy” and “fast” were still in an early paragraph. I replaced them with QR-01, QR-03, and QR-04, and marked the numbers as proposals.
2. One button for compile and run contradicted the brief. Split into FR-06 and FR-07.
3. I had almost treated class sharing and local save as the same feature. Sharing stays out. FR-16 stays in. Export is only a should, because nobody has chosen a file format.
4. Sample output could pass a lecture demo while looking like a real compile. FR-17 requires the sample label on every such result.

## Manual edits after the discussion

- Added the course-notes list at the top of `REQUIREMENTS.md` and the Sep 17 agile note.
- Reworded A1 so candidate `lam` / `fix` / `let` text is sample-only.
- Tightened FR-08, FR-09, and FR-13 against the Sep 22 error and scope rules.
- Left U1 unresolved instead of inventing a timeout.
