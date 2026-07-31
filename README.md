# 🧠 Learning Agent

> An AI-powered tutor that searches the internet and teaches you programming topics using the proven science of learning — with quizzes, spaced repetition, and structured lessons.

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [How It Works — The Big Picture](#2-how-it-works--the-big-picture)
3. [The Science Behind It](#3-the-science-behind-it)
4. [Setup & Installation](#4-setup--installation)
5. [How to Run It](#5-how-to-run-it)
6. [What Happens When You Run It](#6-what-happens-when-you-run-it)
7. [The Lesson Structure](#7-the-lesson-structure)
8. [How the Code Is Organized](#8-how-the-code-is-organized)
9. [Deep Dive: Every Function Explained](#9-deep-dive-every-function-explained)
10. [How the AI (Claude) Works](#10-how-the-ai-claude-works)
11. [How the Database Works](#11-how-the-database-works)
12. [How Spaced Repetition Works](#12-how-spaced-repetition-works)
13. [The Libraries We Use](#13-the-libraries-we-use)
14. [Key Programming Concepts Used](#14-key-programming-concepts-used)
15. [What Each File Does](#15-what-each-file-does)
16. [Common Questions](#16-common-questions)
17. [Ideas for What to Build Next](#17-ideas-for-what-to-build-next)

---

## 1. What Is This?

This is a **terminal application** — a program you run in the command line (the black window with text). It is not a website or a phone app. It runs entirely on your own computer.

Think of it as having a personal tutor who:

- **Never gets tired** of explaining things
- **Looks up the very latest information** before teaching you (no outdated knowledge)
- **Structures every lesson** using techniques proven by learning science
- **Quizzes you at the end** (because testing yourself is the most powerful memory technique)
- **Remembers when to remind you** to review topics before you forget them

The "tutor" is Claude — an AI made by a company called Anthropic. Our script is the glue that connects you to Claude, gives Claude its instructions, displays the results beautifully, and saves your progress.

---

## 2. How It Works — The Big Picture

Here is the complete journey every time you use the agent:

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR TERMINAL                            │
│                                                                 │
│  You type: "Python decorators"                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     agent.py (our script)                       │
│                                                                 │
│  Builds a message: "Teach me Python decorators.                 │
│  Search the web first. Follow your lesson structure."           │
└────────────────────────┬────────────────────────────────────────┘
                         │  sent over the internet
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               Anthropic's Servers (Claude lives here)           │
│                                                                 │
│  Claude reads the message and decides: "I should search first"  │
│                                                                 │
│  Claude uses web_search tool → searches the internet            │
│  Claude reads the search results                                │
│  Claude writes a structured lesson                              │
└────────────────────────┬────────────────────────────────────────┘
                         │  lesson text returned
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     agent.py (our script)                       │
│                                                                 │
│  Displays the lesson beautifully in your terminal               │
│  Asks Claude to extract the 3 quiz questions                    │
│  Shows you each question and waits for your answer              │
│  Sends your answers to Claude for grading                       │
│  Displays feedback and your score                               │
│  Saves topic + score + next review date to the database         │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
              Next time you open the agent:
              "You have 1 topic due for review: Python decorators"
```

---

## 3. The Science Behind It

This agent is not just a chatbot. It is specifically designed around cognitive science research on how humans learn and remember things.

### The Forgetting Curve (Hermann Ebbinghaus, 1885)

Ebbinghaus discovered that memory fades in a predictable pattern:

```
Memory
  │
100%│ ████  ← You learn something
   │     ██
 70%│       ███
   │          ████
 40%│              ███████
   │                      █████████████
 10%│                                    ──────────────────
   └────────────────────────────────────────────────────── Time
       1hr   1day  2days  1wk   2wks  1month
```

The solution: **review just before you forget**. Each time you review, the curve flattens — you remember for longer. This is spaced repetition.

### The Six Learning Techniques Used

| Technique | The Research | Where We Use It |
|---|---|---|
| **Feynman Technique** | Richard Feynman (physicist) said: if you can't explain it simply, you don't understand it. Forcing simple explanations reveals gaps in knowledge. | "Big Picture" section of every lesson |
| **Chunking** | George Miller (1956) found humans can hold 7±2 items in working memory. Breaking information into 3-5 chunks prevents cognitive overload. | "Core Concepts" section — always 3-5 items |
| **Dual Coding** | Allan Paivio (1971) found that combining words with visuals/examples creates two memory traces, making recall twice as likely. | Every concept paired with a code example AND an analogy |
| **Active Recall** | Henry Roediger & Jeffrey Karpicke (2006) — being *tested* on material improves retention far more than re-reading. The act of *retrieving* a memory strengthens it. | The quiz at the end of every lesson |
| **Spaced Repetition** | Based on Ebbinghaus's forgetting curve — reviewing at increasing intervals (1, 3, 7, 14, 30 days) is the most efficient way to move knowledge into long-term memory. | The database schedules and reminds you |
| **Elaborative Interrogation** | Asking "why does this work?" forces deeper processing of the material, creating stronger connections in the brain. | "Common Mistakes" and "Aha Moment" sections |

---

## 4. Setup & Installation

### What You Need First

- **Python 3.10 or newer** — the programming language the script is written in
- **An Anthropic API key** — your personal key to access Claude (get one at console.anthropic.com)
- **A terminal** — the command-line interface on your computer

### Step-by-Step Setup

**Step 1 — Go to the project folder**
```bash
cd ~/learning-agent
```
`cd` means "change directory." It moves you into the learning-agent folder.

**Step 2 — Create a virtual environment**
```bash
python -m venv venv
```
A virtual environment is an isolated Python installation just for this project. It prevents package conflicts between different projects. Think of it as a clean room specifically for this app.

**Step 3 — Activate the virtual environment**
```bash
# On Mac / Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```
You'll see `(venv)` appear at the start of your terminal prompt when it's active.

**Step 4 — Install the required libraries**
```bash
pip install -r requirements.txt
```
`pip` is Python's package manager (like an app store for Python libraries). This reads the `requirements.txt` file and installs everything listed in it.

**Step 5 — Set your API key**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```
This stores your API key as an environment variable — a value that programs can read from the system. Never paste your API key directly into the code.

---

## 5. How to Run It

```bash
python agent.py
```

That's it. Python reads `agent.py` from top to bottom and executes every instruction.

---

## 6. What Happens When You Run It

Here is a detailed walkthrough of a complete session:

### Screen 1 — Welcome Banner
```
╭────────────────────────────────────────╮
│  🧠 Learning Agent                     │
│  Teaches programming using the         │
│  science of learning                   │
╰────────────────────────────────────────╯
```

### Screen 2 — Due Reviews (if any)
If you have studied topics before and they are due for review:
```
📅 You have 2 topic(s) due for review:
  • python decorators (reviewed 1x, score: 85%)
  • async/await (reviewed 0x, score: 70%)

Review a due topic first? [y/N]:
```

### Screen 3 — Topic Input
```
What topic do you want to learn?:
```
You type something like: `Python decorators` and press Enter.

### Screen 4 — Loading
```
⠸ Claude is searching and thinking...
```
A spinner animation plays while Claude searches the web and writes your lesson (usually 20-60 seconds).

### Screen 5 — The Lesson
A full, formatted lesson appears with sections, code examples, and explanations. It looks like a mini textbook page with colors, headers, and syntax-highlighted code.

### Screen 6 — Quiz Prompt
```
Ready for the quiz? (Active recall boosts retention by 50%) [Y/n]:
```

### Screen 7 — Quiz Questions (one at a time)
```
Answer these questions from memory — don't scroll up!

Q1: What is the primary purpose of a Python decorator?
Your answer:
```

### Screen 8 — Quiz Feedback
```
──────────────────── Quiz Results ────────────────────

**Q1:** ✅ Correct! A decorator modifies the behavior of a function...
**Q2:** ⚠️ Partially correct. You got the concept right but...
**Q3:** ❌ The answer is...

Great effort! You understood the core concept well.
```

### Screen 9 — Score & Next Steps
```
Quiz complete! Score: 67%
Good effort! Review again tomorrow to solidify it. 📚

Progress saved to /home/michael/.learning_agent/progress.db
Happy learning! 🚀
```

---

## 7. The Lesson Structure

Every lesson Claude generates follows this exact template. Each section maps to a learning science technique:

```
## 🎯 Why This Matters
   PURPOSE: Motivation. Your brain learns better when it knows why something matters.
   LENGTH: 1-2 sentences. Short and punchy.

## 🗺️ The Big Picture
   PURPOSE: Feynman Technique. Simple explanation before any jargon.
   LENGTH: 2-3 sentences. No technical terms yet.

## 🧩 Core Concepts (Chunked)
   PURPOSE: Chunking. Break into exactly 3-5 digestible pieces.
   FORMAT: Each concept = one sentence + optional code snippet.

## 💡 The "Aha" Moment
   PURPOSE: Mental model + analogy. The insight that makes it "click."
   FORMAT: A comparison to something from everyday life.

## 🔥 Real Example
   PURPOSE: Dual Coding. Seeing the concept in working code.
   LENGTH: Under 20 lines. Every comment explains the "why", not just the "what."

## ⚡ Common Mistakes
   PURPOSE: Elaborative Interrogation. Anticipates where your thinking might go wrong.
   LENGTH: 2-3 mistakes, kept brief.

## 🧠 Quick Quiz (Active Recall)
   PURPOSE: Testing Effect. Retrieval practice strengthens memory.
   FORMAT: 3 questions with hidden answers.

## 🚀 What to Learn Next
   PURPOSE: Interleaving. Connects this topic to related concepts.
   FORMAT: 2-3 topic suggestions that naturally follow.
```

---

## 8. How the Code Is Organized

The entire agent lives in one file: `agent.py`. It is organized into 7 logical sections:

```
agent.py
│
├── Section 1: IMPORTS
│   └── Loads all the external libraries the script needs
│
├── Section 2: VISUAL THEME
│   └── Defines colors for the terminal output
│
├── Section 3: DATABASE SETUP
│   ├── DB_PATH     — where the database file lives
│   ├── init_db()   — creates the database/table if they don't exist
│   ├── save_progress() — saves a topic and schedules next review
│   └── get_due_reviews() — finds topics you need to review today
│
├── Section 4: SYSTEM PROMPT
│   └── LESSON_SYSTEM_PROMPT — Claude's instructions (the "briefing")
│
├── Section 5: TEACHING FUNCTION
│   └── teach_topic() — runs the agentic loop, returns the lesson text
│
├── Section 6: QUIZ FUNCTION
│   └── run_quiz() — extracts questions, runs quiz, grades answers, returns score
│
└── Section 7: MAIN FUNCTION
    └── main() — the director that coordinates everything
```

---

## 9. Deep Dive: Every Function Explained

### `init_db()`

**What it does:** Creates the SQLite database file and the `learned_topics` table if they don't already exist. Called before any database operation to ensure the database is ready.

**When it runs:** Every time we need to use the database (inside `save_progress` and `get_due_reviews`).

**The table it creates:**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incrementing unique identifier |
| `topic` | TEXT | The topic name (stored lowercase) |
| `learned_at` | TEXT | ISO date/time when you last studied it |
| `next_review` | TEXT | ISO date/time when you should review it again |
| `review_count` | INTEGER | How many times you've reviewed it (starts at 0) |
| `quiz_score` | REAL | Your most recent quiz score (0.0 to 1.0) |

---

### `save_progress(topic, quiz_score)`

**What it does:** Saves your quiz result and calculates when you should review the topic again.

**Logic flow:**
```
Is this topic already in the database?
       │
   YES ─┤─ Get the current review_count
       │  ─ Look up the next interval from the schedule: [1, 3, 7, 14, 30, 60]
       │  ─ next_review = now + that many days
       │  ─ UPDATE the existing row
       │
   NO  ─┤─ next_review = tomorrow (first time = 1 day)
          ─ INSERT a new row
```

**The spacing schedule:**

```
Review count → Days until next review
     0       →     1 day   (you just learned it)
     1       →     3 days
     2       →     7 days  (1 week)
     3       →    14 days  (2 weeks)
     4       →    30 days  (1 month)
     5+      →    60 days  (2 months, maximum interval)
```

---

### `get_due_reviews()`

**What it does:** Queries the database for any topics where `next_review` is in the past (overdue) or right now.

**Returns:** A list of dictionaries, one per due topic. Example:
```python
[
    {"topic": "python decorators", "next_review": "2025-01-14T10:30:00", "review_count": 1, "score": 0.85},
    {"topic": "async/await",       "next_review": "2025-01-13T09:00:00", "review_count": 0, "score": 0.70},
]
```

---

### `teach_topic(topic)`

**What it does:** The heart of the application. Sends a request to Claude with the topic and the lesson system prompt, manages the back-and-forth conversation while Claude searches the web, and collects the final lesson text.

**The agentic loop in detail:**

```
ITERATION 1:
  We send:  "Teach me Python decorators. Search the web first."
  Claude:   Decides to search. Responds with stop_reason="tool_use"
  We:       Add Claude's response to history. Send "tool completed" message.

ITERATION 2:
  We send:  The full history (including tool result)
  Claude:   Reads search results. Writes the lesson. Responds with stop_reason="end_turn"
  We:       Collect the lesson text. Break out of the loop.
```

**Stop reasons and what they mean:**

| `stop_reason` | Meaning | What we do |
|---|---|---|
| `"end_turn"` | Claude finished naturally | Break out of loop. We're done. |
| `"tool_use"` | Claude wants to use web search | Add its message to history, send tool acknowledgment, loop again |
| `"pause_turn"` | Server-side tool hit its iteration limit | Add message to history, loop again (Claude resumes automatically) |

**Parameters sent to Claude:**

| Parameter | Value | Why |
|---|---|---|
| `model` | `"claude-opus-4-6"` | The most capable Claude model — best lesson quality |
| `max_tokens` | `8000` | Allows up to ~6000 words for the lesson |
| `thinking` | `{"type": "adaptive"}` | Claude reasons carefully before answering |
| `system` | `LESSON_SYSTEM_PROMPT` | Claude's instructions for how to teach |
| `tools` | `[web_search]` | Allows Claude to search the internet |
| `messages` | The conversation history | The full back-and-forth so far |

---

### `run_quiz(lesson_text)`

**What it does:** Takes the lesson text and runs a 3-question quiz. Returns a score from 0.0 to 1.0.

**Step by step:**

1. **Extract questions** — sends the lesson to Claude with a structured output format (JSON schema), so Claude returns the questions in a predictable, parseable format.

2. **Display questions** — shows each question to the user one at a time and collects their answers.

3. **Grade answers** — sends the lesson, questions, and user answers back to Claude and asks for feedback on each answer.

4. **Get score** — asks Claude to summarize the feedback as a single number between 0.0 and 1.0.

**Why use structured output (JSON schema) for question extraction?**

Without it, Claude might return:
- "1. What is a decorator? 2. How do you apply one?"
- "- What is a decorator?\n- How do you apply one?"
- "Q1: What is a decorator? Q2: How do you apply one?"

All different formats, all hard to parse reliably. With a JSON schema, Claude always returns:
```json
{"questions": [{"q": "What is a decorator?"}, {"q": "How do you apply one?"}]}
```
One predictable format that code can extract reliably every time.

---

### `main()`

**What it does:** The "director" function. Runs everything in the right order.

**Sequence:**
```
1. Print welcome banner
2. Query database for due reviews
3. If reviews are due → offer to review one
4. Ask what topic to study (or use chosen due topic)
5. Validate input (don't proceed if topic is empty)
6. Call teach_topic() → get lesson
7. Display lesson
8. Ask if ready for quiz
9. If yes → call run_quiz() → get score → display feedback
10. Call save_progress() with topic and score
11. Print goodbye message
```

---

## 10. How the AI (Claude) Works

### What Is an API?

API stands for "Application Programming Interface." It is a way for one program to talk to another program over the internet.

Imagine a restaurant:
- **You** = our script
- **The waiter** = the Anthropic API (takes our order, brings the food)
- **The kitchen** = Claude (does the actual work)
- **The menu** = the API documentation (what you're allowed to order)

We "order" by sending HTTP requests (internet messages) to Anthropic's servers. They process the request with Claude and send back a response.

### How We Communicate With Claude

Every API call follows this structure:

```python
response = client.messages.create(
    model="claude-opus-4-6",    # Which AI model to use
    max_tokens=8000,            # Maximum response length
    system="You are a tutor",   # Secret instructions
    messages=[                  # The conversation history
        {"role": "user", "content": "Teach me decorators"},
    ]
)
```

Claude returns a `response` object. The actual text is in:
```python
response.content[0].text   # The first content block's text
```

### What Is a System Prompt?

A system prompt is a hidden set of instructions you give Claude before the conversation starts. The user (you, in this case) never sees it — only its effects.

In this agent, the system prompt tells Claude:
- You are a programming tutor
- Always search the web first
- Follow this exact lesson structure: Why It Matters → Big Picture → Core Concepts → ...
- Always generate exactly 3 quiz questions
- Use analogies and code examples

### What Are Tools?

Tools are extra capabilities we grant Claude beyond just text generation. Without tools, Claude only knows what was in its training data (which has a cutoff date). With tools, it can act in the world.

We use one tool: **web_search** (`web_search_20260209`).

When Claude decides to search:
1. Claude's response contains a `tool_use` block
2. Anthropic's servers perform the actual web search
3. The results are passed back to Claude automatically
4. Claude reads the results and continues writing

This is a "server-side tool" — we don't write any search code. Anthropic handles it entirely.

### What Is Adaptive Thinking?

We set `thinking={"type": "adaptive"}` in our API calls. This tells Claude to reason step-by-step before answering, like a person who thinks out loud before speaking. The "adaptive" part means Claude decides how much thinking to do based on complexity — simple topics get less thinking, complex topics get more.

The thinking itself is usually hidden from the output, but it significantly improves the quality of the lesson.

---

## 11. How the Database Works

We use **SQLite** — a database engine built directly into Python. No separate database server needed. The entire database is stored as a single file on your computer.

**Where the file lives:**
```
/home/your-username/.learning_agent/progress.db
```

**What SQLite is:**
Think of it like an extremely organized spreadsheet that you can search very quickly. It speaks SQL (Structured Query Language) — a standard language for interacting with databases.

**The SQL commands we use:**

| Command | What it does | When we use it |
|---|---|---|
| `CREATE TABLE IF NOT EXISTS` | Creates a table only if it doesn't exist | When initializing the database |
| `SELECT ... WHERE` | Finds rows matching a condition | Checking for due reviews, checking if a topic exists |
| `INSERT INTO ... VALUES` | Adds a new row | When studying a topic for the first time |
| `UPDATE ... SET ... WHERE` | Modifies an existing row | When reviewing a topic you've seen before |

**Example: What a database SELECT looks like**
```sql
SELECT topic, next_review, review_count, quiz_score
FROM learned_topics
WHERE next_review <= '2025-01-15T10:30:00'
ORDER BY next_review
```
"Give me all columns from `learned_topics` where the next review date is in the past, sorted by oldest first."

---

## 12. How Spaced Repetition Works

This is the system that turns the agent from a one-time tutor into a long-term learning companion.

### The Problem It Solves

Without spaced repetition:
- Day 1: Learn Python decorators ✅
- Day 7: Vaguely remember them 😐
- Day 30: Almost completely forgotten 😞
- Day 60: Back to square one 😢

With spaced repetition:
- Day 1: Learn Python decorators ✅ → Schedule review for Day 2
- Day 2: Quick review ✅ → Schedule for Day 5
- Day 5: Quick review ✅ → Schedule for Day 12
- Day 12: Quick review ✅ → Schedule for Day 26
- Day 26: Quick review ✅ → Schedule for Day 56

Each review resets the forgetting curve at a higher baseline. Over 2 months, you've done 5 reviews in the time you would have forgotten it once. Eventually it moves into true long-term memory.

### The Review Schedule

```
review_count (how many times reviewed) → days until next review
        0  →   1 day   (brand new topic)
        1  →   3 days
        2  →   7 days  (1 week)
        3  →  14 days  (2 weeks)
        4  →  30 days  (1 month)
        5+ →  60 days  (2 months — maximum spacing)
```

### Score-Based Feedback

The quiz score also influences feedback (though not the interval, to keep the implementation simple):

| Score | Feedback | Implication |
|---|---|---|
| 80% or above | "Excellent! Next review in 3 days." | Knowledge is solid |
| 50% – 79% | "Good effort! Review again tomorrow." | Understanding, but shaky |
| Below 50% | "Re-read the lesson and review again tomorrow." | Needs another pass |

---

## 13. The Libraries We Use

### `anthropic` — Talking to Claude

The official Python library for the Claude API. Handles authentication, HTTP requests, response parsing, retries, and error handling.

```python
import anthropic
client = anthropic.Anthropic()  # Reads ANTHROPIC_API_KEY from environment
response = client.messages.create(...)
```

Without this library, we would need to write raw HTTP requests, handle network errors manually, parse JSON responses ourselves, and manage API keys in headers. The library does all of this for us.

### `rich` — Beautiful Terminal Output

A library that makes terminal output colorful and readable. Plain Python `print()` only outputs plain white text. `rich` adds:

| Feature | What it does | Example |
|---|---|---|
| `Console` | The main output object | `console.print("[bold]Hello[/bold]")` |
| `Markdown` | Renders markdown formatting | `## Header` becomes large bold text |
| `Panel` | Draws a box around content | The welcome screen box |
| `Rule` | Draws a horizontal divider line | Section separators |
| `Prompt` | Gets text input from the user | `Prompt.ask("Enter topic:")` |
| `Confirm` | Gets yes/no from the user | `Confirm.ask("Ready for quiz?")` |
| `Theme` | Defines custom color names | `[info]`, `[success]`, `[error]` |
| `.status()` | Spinning animation while waiting | The loading spinner |

### `sqlite3` — The Database

Built into Python — no installation needed. Provides an interface to SQLite databases. We use it to store learning progress permanently between sessions.

### `json` — Parsing Structured Data

Also built into Python. Converts between JSON text (what Claude returns for structured output) and Python dictionaries/lists (what our code uses).

```python
# JSON text → Python dictionary
data = json.loads('{"questions": [{"q": "What is X?"}]}')
# data["questions"][0]["q"] == "What is X?"
```

### `datetime` and `timedelta` — Date Math

Built into Python. Used for calculating review dates.

```python
from datetime import datetime, timedelta
now = datetime.now()                    # current date and time
next_review = now + timedelta(days=7)   # 7 days from now
```

### `pathlib.Path` — File Paths

Built into Python. A cleaner way to work with file and folder paths that works on all operating systems (Windows uses `\`, Mac/Linux use `/` — Path handles both).

```python
from pathlib import Path
DB_PATH = Path.home() / ".learning_agent" / "progress.db"
# Result: /home/michael/.learning_agent/progress.db (on Linux)
#         C:\Users\michael\.learning_agent\progress.db (on Windows)
```

---

## 14. Key Programming Concepts Used

### Functions

A function is a named block of code you can run by calling its name. Like a saved recipe.

```python
def save_progress(topic, quiz_score):  # "def" defines a function
    # ... code here ...

save_progress("decorators", 0.85)  # this "calls" (runs) the function
```

### Type Hints

The `: str` and `-> float` annotations tell you what type of data a function expects and returns. Python doesn't enforce them, but they make the code much easier to understand.

```python
def save_progress(topic: str, quiz_score: float) -> None:
#                 ↑ expects text   ↑ expects decimal   ↑ returns nothing
```

### The While Loop (Agentic Loop)

Runs a block of code repeatedly until a condition becomes false.

```python
while iteration < max_iterations:
    # ... send request to Claude ...
    if response.stop_reason == "end_turn":
        break  # exit the loop
    iteration += 1
```

### F-strings (Formatted Strings)

A way to embed variables directly inside text strings.

```python
topic = "Python decorators"
message = f"Teach me about: {topic}"
# Result: "Teach me about: Python decorators"
```

### List Comprehensions

A compact way to build a list by transforming another list.

```python
# Long way:
result = []
for r in rows:
    result.append({"topic": r[0], "score": r[3]})

# Short way (list comprehension):
result = [{"topic": r[0], "score": r[3]} for r in rows]
```

### Context Managers (`with` statement)

Automatically handles setup and cleanup for resources like files, database connections, and spinners.

```python
with console.status("Loading..."):
    # do work here
# spinner automatically stops when this block ends, even if an error occurs
```

### Try/Except (Error Handling)

Catches errors so the program doesn't crash.

```python
try:
    score = float(text)      # might fail if text is not a number
except ValueError:
    score = 0.7              # use a default value instead of crashing
```

### Constants (ALL_CAPS Variables)

Variables named in ALL_CAPS are conventionally treated as constants — values that should not change while the program runs. Python doesn't enforce this, but it's a widely followed convention.

```python
LESSON_SYSTEM_PROMPT = "You are a tutor..."   # never changes
DB_PATH = Path.home() / ".learning_agent"      # never changes
```

---

## 15. What Each File Does

```
learning-agent/
│
├── agent.py           ← The entire application (one file)
│                        Contains all functions, the database logic,
│                        the system prompt, and the main() entry point.
│
├── requirements.txt   ← The list of Python libraries to install
│                        pip install -r requirements.txt reads this file.
│                        Contents:
│                          anthropic>=0.40.0
│                          rich>=13.0.0
│
├── README.md          ← This file. Documentation.
│
└── venv/              ← Virtual environment (created by you during setup)
                         Contains isolated Python installation + libraries.
                         Do NOT edit files inside here manually.
                         NOT committed to git (if you use version control).
```

**Database file (created automatically when you first run the agent):**
```
~/.learning_agent/
└── progress.db        ← SQLite database with your learning history
                         ~ means your home directory
                         The dot prefix hides it from normal file listings
```

---

## 16. Common Questions

**Q: How much does it cost to use?**

It uses the Claude API which charges per token (roughly per word). A typical lesson costs approximately $0.05 to $0.15 (US cents, not dollars). Usage depends on lesson length and how many web searches Claude performs.

**Q: Does it work without internet?**

No. The agent needs the internet to:
1. Contact Anthropic's servers to run Claude
2. Claude needs the internet to use the web_search tool

**Q: Where is my progress saved?**

In a SQLite database at `~/.learning_agent/progress.db`. You can open this file with any SQLite viewer (like DB Browser for SQLite) to see your learning history.

**Q: Can I use it for topics other than programming?**

Yes. The system prompt focuses on programming, but you can type any topic. The lesson structure and quiz will still work. However, Claude's instructions are biased toward programming — other topics may not include code examples.

**Q: What if the lesson is cut off or incomplete?**

Try asking a more specific topic. Very broad topics like "machine learning" may result in very long lessons that hit the `max_tokens` limit. Try "gradient descent in machine learning" instead.

**Q: Can I run it multiple times?**

Yes. Each run is independent. Your progress accumulates in the database across all runs.

---

## 17. Ideas for What to Build Next

Once you're comfortable with how this works, here are natural next steps:

| Feature | What It Would Do | Skills You'd Learn |
|---|---|---|
| **Voice output** | Read the lesson aloud using text-to-speech | `pyttsx3` or `openai` TTS library |
| **Web UI** | Show the lesson in a browser instead of terminal | `streamlit` library (very beginner-friendly) |
| **Anki export** | Export your quiz questions to Anki flashcard format | File I/O, Anki's file format |
| **Learning path** | Suggest a curriculum based on what you've already learned | More complex Claude prompting |
| **Multiple quizzes** | Track individual question performance, not just overall score | More database tables and SQL |
| **Lesson history** | Re-read past lessons | Reading from the database + displaying stored text |
| **Topic search** | Search through your learned topics | SQL LIKE queries |
| **Email reminders** | Email yourself when a topic is due | `smtplib` (Python's email library) |
| **Deploy as a web app** | Access it from your phone or anywhere | Flask/FastAPI, cloud hosting (Render, Railway, Fly.io) |

---

## Quick Reference

```bash
# Setup (one time only)
cd ~/learning-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"

# Run
python agent.py

# View your progress database
sqlite3 ~/.learning_agent/progress.db "SELECT topic, quiz_score, next_review FROM learned_topics;"
```

---

*Built with Python · Claude API (claude-opus-4-6) · Rich · SQLite*
