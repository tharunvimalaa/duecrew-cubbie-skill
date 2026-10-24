# DueCrew

A Cubbie Skill that rescues a group project. A student texts Cubbie their messy group chat and the assignment
instructions, and Cubbie replies with a Project Rescue Plan:

- the project name and deadline, with its source (a disagreement between sources is flagged, not guessed)
- tasks taken from the instructions and the chat
- commitments people actually made, quoted as evidence
- owners someone suggested who never said yes
- unassigned tasks and blockers
- recommended next steps
- a ready-to-forward message asking teammates to confirm
- an offer of a personal reminder, created only after the student says yes

DueCrew never invents owners, deadlines or agreements, never treats a suggestion as a commitment, and never
contacts teammates. Cubbie talks only to its student, who forwards the drafted message themselves.

The Skill is instructions only (`duecrew/SKILL.md`): no scripts, packages, keys or backend. It uses Cubbie's
existing abilities: reading pasted text, screenshots and documents, Canvas (when connected, only to verify the
deadline) and reminders.

## Install

On Cubbie, text it the link to the `duecrew` folder of this repository:

```text
https://github.com/tharunvimalaa/duecrew-cubbie-skill/tree/main/duecrew
```

Cubbie asks before fetching it. Reply "yes", and the Skill is available from your next message.

In Claude Code, copy the folder into your skills directory:

```bash
cp -r duecrew ~/.claude/skills/duecrew
```

## Example

Text Cubbie:

```text
Cubbie, rescue my group project. Here's our group chat and assignment.

ASSIGNMENT (BIO 210, Group Research Poster): lit review, methods, results figures, poster layout.
Due Friday, October 30, 11:59 pm.

Priya: ok so we need lit review, methods, figures, and the poster layout
Maya: I'll do the lit review, will have it done by Wednesday
Priya: Leo maybe you could do the figures since you have the data?
Priya: also someone needs to do methods
```

Cubbie replies (trimmed):

```text
Project Rescue Plan: BIO 210 Group Research Poster
Deadline: Friday, October 30, 11:59 pm (assignment instructions)

Committed (they said yes):
- Lit review: Maya ("I'll do the lit review, will have it done by Wednesday")
Proposed, not agreed:
- Results figures: Leo (suggested by Priya, no yes yet)
Unassigned:
- Methods section
- Poster layout
...
```

Then it sends a message to forward to the group, and asks whether you want a reminder to check who replied.

## Local tests

`tests/scenarios/` holds five student texts:

1. `1-commitment-vs-tentative`: one explicit commitment (Maya) and one tentative assignment (Leo)
2. `2-conflicting-deadlines`: the instructions say Nov 6 and the chat says Nov 8
3. `3-no-agreed-owners`: four tasks, nobody agreed to any
4. `4-assignment-only`: instructions but no group chat, so the plan lists every task as unassigned and drafts a call for volunteers
5. `5-withdrawn-commitment`: a teammate takes a task, then backs out of it later in the chat

`tests/run_tests.py` sends each one to Claude Code (`claude -p`) with `SKILL.md` loaded, saves the reply in
`tests/output/`, and checks it: every label is present and in order, each person is in the right section (for
example, Leo must not be under Committed), a deadline conflict is flagged, there is no Markdown, and the reply
doesn't claim it contacted anyone or set a reminder.

Canvas and reminders exist only inside Cubbie, so these tests cover the reasoning and the reply format. Test the
full flow by texting the Skill link to your own Cubbie.

Requirements: Python 3.9+ and the Claude Code CLI, signed in.

```bash
python3 tests/run_tests.py               # run all five scenarios (about a minute)
python3 tests/run_tests.py 2             # run one scenario
python3 tests/run_tests.py --check-only  # re-check the saved replies, no model call
```

Validate the Skill folder with the Cubbie toolkit's validator (it needs PyYAML):

```bash
python3 <cubbie-skill-creator>/scripts/validate_cubbie_skill.py duecrew
```
