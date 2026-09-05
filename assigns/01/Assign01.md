# Assignment #1
GitHub Repository and AI-Assisted Code Translation

# Due time: 11:59PM, the 8th of September, 2026

## Objective

The purpose of this assignment is to gain practical experience with
Git, GitHub, and AI-assisted software development. You will create a
GitHub repository, place a small program in the repository, use an AI
coding assistant to translate the program into another programming
language, and evaluate the quality of the generated translation.

This assignment emphasizes that AI-generated code should be treated as
a draft that must be reviewed, tested, and corrected by the
programmer.

## Tasks

1. **Create a GitHub repository**

   Please follow the instructions given in README.md.

2. **Add the original program**

   Obtain the source program provided by the instructor and place it in your repository:

   https://ats-lang.github.io/FROZEN000/DOCUMENT/INT2PROGINATS/HTML/INT2PROGINATS-BOOK-onechunk.html#example-the-eight-queens-puzzle

3. **Use AI to translate the program**

   Use AI the original program into the target programming language Python~3.

   Your prompt should ask the AI to preserve the behavior of the original program as closely as possible.

   You may ask follow-up questions or request corrections if the initial translation is incomplete or incorrect.

4. **Record your interaction with the AI**

   Create a file named `AI-TRANSCRIPT.md`.

   In this file, record:

   - The AI system you used.
   - Your initial prompt.
   - Important follow-up prompts.
   - Significant corrections suggested by the AI.
   - Any changes you made manually after reviewing the generated code.

   You do not need to include unrelated conversation with the AI.

5. **Review the generated code**

   Do not assume that the AI-generated translation is correct.

   Examine the translated program for issues such as:

   - Incorrect syntax.
   - Incorrect interpretation of the original program.
   - Differences in data types or language semantics.
   - Missing functions or functionality.
   - Improper library usage.
   - Poor or unnecessarily complicated code.

   Correct any problems you find.

6. **Test the translation**

   Compile or run both the original program and the translated program.

   Develop several test cases and compare their outputs.

   Whenever possible, include:

   - A normal input case.
   - A boundary or unusual case.
   - At least one additional test of your own design.

   Record your tests and results in the repository.

7. **Use Git throughout the assignment**

   Make multiple meaningful commits rather than completing the entire assignment in one commit.

   For example:

   - `Add original source program`
   - `Add initial AI-generated translation`
   - `Fix translation errors`
   - `Add test cases`
   - `Document AI-assisted development process`

   Your repository history should make it possible to see how the solution developed.

8. **Write a short reflection**

   Add a section titled **AI Reflection** to your `README.md`.

   In approximately 200–400 words, discuss:

   - What the AI did well.
   - What mistakes or weaknesses you found.
   - What you had to understand yourself in order to verify the translation.
   - Whether the AI-generated version could have been trusted without testing.
   - How AI affected the amount or nature of the work you performed.

## Required Repository Contents

   Your final repository should contain:

     - The original source program.
     - The translated source program.
     - `README.md`.
     - `AI-TRANSCRIPT.md`.
     - Test cases or a description of the tests performed.
     - Any scripts or files needed to compile and run the programs.

   The repository should also contain a meaningful Git commit history.

## Submission

Submit your work into the designated Gradescope folder.

Before submitting, verify that the instructor can access the
repository. If the repository is private, grant the instructor the
required access.

## Grading

The assignment will be evaluated based on the following criteria:

- **Repository setup and Git usage — 20%**
- **Quality and completeness of the code translation — 25%**
- **Testing and verification — 25%**
- **Documentation of AI usage — 15%**
- **Reflection and analysis — 15%**

A successful submission is not simply one in which the AI produces
working code. The goal is to demonstrate that you can use AI as a
software-development tool while independently evaluating, testing, and
taking responsibility for the resulting program.
