# Requirements specification: LAMBDA testing environment

Student: Anay Sharma

Source brief: `assigns/03/LAMBDA-UI-informal-requirements.md`  
Status: first-version specification. No stakeholder answers have been received beyond that brief. Assumptions below are proposals, not stakeholder decisions.

## 1. Purpose

Provide a local, browser-based environment where a course participant can edit a LAMBDA program, ask a separate compiler to check or run it, read the outcome, and keep named examples as repeatable tests. The environment is a client of the compiler. It does not implement the language.

## 2. Stakeholders and goals

| Stakeholder | Main goals |
| --- | --- |
| Student writing programs | Start from an example, edit, run, and understand errors without installing language tools by hand. |
| Student changing the compiler | Re-run a saved collection of tests after a compiler change and see which cases still match their expected outcomes. |
| Instructor in lecture | Open a known example, change an input, and show the new result without losing the original example or waiting on interface setup. |
| Compiler provider | Offer a stable request/response interface. Building the compiler is outside this project. |

## 3. System boundary and scope

**Inside version 1**

- A page opened in a normal browser on the same computer as the user.
- An editor, built-in examples, compile-only and run actions, result display, cancel, and a named test collection stored on that browser profile.
- An adapter that talks to either a sample responder or the real compiler through the same request shape.

**Outside version 1**

- Implementing or changing the LAMBDA compiler or its concrete syntax.
- A public website, accounts, authentication, or several people editing one program at the same time.
- Sharing a test collection with the class. The brief says this can wait.
- A full development environment (version control, debugging, project search).

**Environment versus compiler**

The environment sends source text and a mode (`check` or `run`) and displays whatever the compiler returns. Correctness of compilation and execution belongs to the compiler. The environment is responsible for not presenting a compiler-unreachable failure, a cancelled run, or a sample response as if the user’s program had been compiled for real.

## 4. Clarification questions

No replies have been received. Each item states why it matters and how this specification proceeds.

**Q1. What source notation does version 1 accept?**  
The brief says programs are still discussed as Python ASTs and that concrete syntax is unsettled. The editor, examples, file import, and tests all depend on the text the compiler accepts.  
**Assumption A1:** Version 1 sends the editor buffer as text. The compiler interface defines the notation. Until a notation is fixed, only the sample backend is used, and the page states that.

**Q2. Where should programs and tests live if there are no accounts?**  
Refresh and a later session must not drop prepared examples, but the brief does not name a store.  
**Assumption A2:** Data is stored in the browser profile on that machine (local storage or an equivalent browser store). Import and export of a file are also required so a program can move without retyping.

**Q3. Must a long run stop by itself, or only when the user cancels?**  
The brief requires a way to stop a run that may not finish. It does not set a time limit.  
**Unresolved U1:** No automatic timeout is specified. **Assumption A3:** The user can cancel the in-progress request. The page stays interactive while that request is outstanding.

**Q4. What may a test expect?**  
The brief names an integer or Boolean answer, or rejection of an erroneous program. It does not say whether the error text must match.  
**Assumption A4:** A test expects either a run result whose displayed value is an integer or Boolean equal to the recorded value, or a compile rejection (any compile error). Matching the wording of the diagnostic is out of scope for version 1.

**Q5. Are “compile” and “run” separate actions?**  
The brief says the user sometimes only wants to know whether a program compiles.  
**Assumption A5:** The page offers Check (compile, do not execute) and Run (compile, then execute only if compilation succeeds).

**Q6. Which browsers must work?**  
The brief says “a browser students normally use” and does not name products.  
**Assumption A6 (proposal):** Current versions of Chrome, Firefox, Edge, and Safari on the instructor’s and students’ own machines. One active page is supported. Two tabs editing the same stored collection may overwrite each other; that limit is documented in setup notes, not treated as a feature.

**Q7. May sample compiler output appear in lecture?**  
The brief allows sample responses before the compiler exists, if they cannot be mistaken for real results.  
**Assumption A7:** Sample mode is allowed and must be labeled on every result. Connecting the real compiler uses the same request and response fields; the page does not change its actions.

## 5. Functional requirements

Priority: **M** = must for version 1, **S** = should, **W** = wait (not in version 1).

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-01 | M | The user can open the environment in a supported browser on the local computer without creating an account. |
| FR-02 | M | The user can type or paste source text into an editor. |
| FR-03 | M | The user can replace the editor contents with the text of a file chosen from the local computer. |
| FR-04 | M | The user can load a built-in example into the editor. Editing that buffer does not change the built-in example; choosing the example again restores its original text. |
| FR-05 | M | The user can save the current editor text under a name in the browser profile and open that saved text again after a reload and in a later visit with the same profile. |
| FR-06 | M | The user can request Check. The environment sends the current editor text to the compiler in check mode and does not request execution. |
| FR-07 | M | The user can request Run. The environment sends the current editor text in run mode. If the compiler reports a compile error, the environment does not present an execution result. |
| FR-08 | M | After Check or Run, the page shows one of: a successful compile with no execution (Check), a successful execution value (Run), a compile error, a runtime failure, a cancellation, or an environment failure. These outcomes use different labels. |
| FR-09 | M | When the compiler response includes a source location for a compile error, the environment indicates that location in the editor (selection or equivalent visible mark) as well as in the message text. |
| FR-10 | M | If the compiler cannot be contacted, the page labels the outcome as an environment failure, not as a compile error or a runtime failure, and the editor text remains available for a later attempt. |
| FR-11 | M | While a Check or Run request is outstanding, the user can still edit text, load an example, and choose Cancel. Cancel asks the adapter to abandon that request. |
| FR-12 | M | A displayed result names the editor text that was sent (for example a snapshot id or a “stale” marker). If the user edits the buffer after the request starts, the result stays tied to the sent text and is marked as not matching the current buffer. |
| FR-13 | S | When the compiler response includes an AST or generated code, the user can open an inspector for that artifact. The inspector is closed by default and is omitted when the artifact is absent. |
| FR-14 | M | The user can create, rename, edit, and delete a named test. A test stores source text and an expectation: either an integer, a Boolean, or “compile rejection.” |
| FR-15 | M | The user can run every saved test. The page shows a count of passed and failed tests and, for each failure, the test name, expectation, and actual outcome. A failure does not skip the remaining tests. |
| FR-16 | M | Saved programs (FR-05) and the test collection (FR-14) are still present after the page is reloaded. |
| FR-17 | M | The active backend is either Sample or Compiler. In Sample mode every result is labeled “sample, not a compiler result.” Switching to Compiler uses the same Check, Run, and test-run actions. |
| FR-18 | S | The user can download the current editor text, and can download the test collection as one file that can be imported later on a browser that satisfies FR-03 and FR-14. |

## 6. Quality requirements

Targets marked as proposals are not in the brief.

| ID | Pri | Requirement |
| --- | --- | --- |
| QR-01 | M | Check, Run, Cancel, load-example, save, and run-all-tests can each be invoked with the keyboard alone, without a pointer. |
| QR-02 | M | Compile error, runtime failure, environment failure, pass, and fail are each identified by text. Color may be added but is not the only signal. |
| QR-03 | M | **Proposal A8:** On a reference laptop (current mid-range student machine), loading an example, switching the inspector, and updating the editor do not wait on the compiler and become visible within 200 ms. A compiler request may take longer; during that time the page still accepts edit and Cancel (FR-11). |
| QR-04 | M | **Proposal A9:** A person who has the setup notes and a supported browser can open the page and run one built-in example within 15 minutes, without reading compiler source. |
| QR-05 | M | After a reload, the last saved editor text and all saved tests from that profile are unchanged (same names, source, and expectations). |

## 7. External interfaces

**Compiler adapter (dependency).** One request carries: source text, mode (`check` or `run`), and a request id. One response carries: status (`ok`, `compile-error`, `runtime-error`, `cancelled`, `unavailable`), optional value (integer or Boolean), optional message, optional source location, and optional AST or generated-code text. The sample backend returns the same fields and is labeled by the environment, not by hiding the status.

**Browser.** Renders the page, holds FR-05 and FR-16 storage, and offers a file picker and download for FR-03 and FR-18.

**User.** Keyboard and pointer. No account service.

The compiler project is a separate effort. This environment does not require a finished compiler in order to demonstrate Sample mode.

## 8. Priorities

Version 1 must include FR-01–FR-12, FR-14–FR-17, and QR-01–QR-05. Inspector detail (FR-13) and file export of the whole collection (FR-18) should be included if time remains; they are not required to satisfy the lecture and regression stories. Class sharing, accounts, hosted deployment, and collaborative editing wait, matching the brief.

## 9. Acceptance checks

These are future checks, not results from a built system.

**AC-1 (FR-04), normal.** Start with built-in example Factorial unchanged. Load it, change the input literal, Run. Choose Factorial again. Expected: the editor shows the original example text, not the edited copy.

**AC-2 (FR-07, FR-08), normal.** Editor contains a program the compiler runs to integer 6. Choose Run. Expected: the page shows a run success and the value 6, with label “run,” not “check.”

**AC-3 (FR-09), normal.** Compiler returns a compile error at line 2, column 4. Expected: the message states that location and the editor marks line 2, column 4.

**AC-4 (FR-10), failure.** Compiler process is not running. Editor contains any text. Choose Run. Expected: label is environment failure; the text is not described as a program error; the buffer is still the typed text; a later Run is possible after the compiler is started.

**AC-5 (FR-11), failure.** Start Run on a program that does not return. While the request is outstanding, edit the buffer and choose Cancel. Expected: the request ends as cancelled; the new edits remain in the editor; the page accepts another Run.

**AC-6 (FR-12), exceptional.** Start Run. Before the response arrives, change one character. Expected: the result that appears is marked as produced by the text that was sent, and marked as different from the current buffer.

**AC-7 (FR-15), exceptional.** Collection has three tests; the second expects integer 1 but the compiler returns 2. Expected: the summary reports 2 passed and 1 failed; the second test shows expected 1 and actual 2; the third test still has a pass or fail result.

**AC-8 (FR-16), normal.** Save a program and two tests. Reload the page. Expected: the saved program and both tests are listed with the same source and expectations.

## 10. Traceability

| ID | Source |
| --- | --- |
| FR-01 | Brief “Keeping the project manageable”: local, no accounts. |
| FR-02 | “Trying a program”: type or paste. |
| FR-03 | “Students may already have programs saved in files.” |
| FR-04 | Lecture factorial example; “modify an example without losing access to the original.” |
| FR-05 | “keep a program… and return to it later”; A2. |
| FR-06 | “Sometimes I only want to check whether a program compiles”; A5. |
| FR-07 | “At other times, I want to run it and see the answer”; A5. |
| FR-08 | “A compilation error and a failure while running… should not look like the same thing.” |
| FR-09 | “When the compiler reports where the problem occurred… find that place in the source.” |
| FR-10 | “If it cannot reach the compiler… not… their program is wrong”; “keep their work and try again.” |
| FR-11 | “a way to stop it”; “page should remain usable while work is in progress”; A3. |
| FR-12 | “which version produced the result I am seeing.” |
| FR-13 | “inspect… AST or generated code… not… in the way” of a simple run. |
| FR-14 | “Keeping examples as tests”; integer, Boolean, or rejection; A4. |
| FR-15 | “quick summary”; “enough detail”; “one troublesome test should not make the rest… useless.” |
| FR-16 | “refreshing the page” must not drop prepared examples; “another session.” |
| FR-17 | “sample compiler responses… nobody mistakes them”; “connect the real compiler without starting the interface over.” |
| FR-18 | Files already on disk; A2. Should, not must. |
| QR-01 | “main tasks with a keyboard.” |
| QR-02 | “messages should make sense without depending only on colors.” |
| QR-03 | “respond promptly” while the compiler may take longer; proposal A8. |
| QR-04 | “easy to get started”; “setup should be straightforward”; proposal A9. |
| QR-05 | Same passages as FR-16. |

## 11. Review notes

**Issue 1.** The first draft said the tool should be “easy” and “fast.” Those words are not testable. They were replaced by QR-01 (keyboard paths), QR-04 (15-minute setup, labeled as a proposal), and QR-03 (200 ms for non-compiler actions, also a proposal), with compiler time excluded from the UI bound.

**Issue 2.** Check and Run were one button. That conflicts with the brief’s split between “does it compile” and “what does it return.” FR-06 and FR-07 are separate, and FR-07 does not show an execution value when compilation fails.

**Issue 3.** Persistence and class sharing were easy to merge. The brief treats sharing as optional and treats losing examples on refresh as unacceptable. FR-16 is in version 1; sharing stays out of scope. Export (FR-18) is only a should, so version 1 does not depend on a file format the stakeholder has not chosen.

**Issue 4.** Sample results could satisfy a demo while looking like real compiler output. FR-17 requires the sample label on every such result and the same actions when the real adapter is attached.
