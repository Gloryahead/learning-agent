"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🧠 LEARNING AGENT                                   ║
║              Teaches programming using the science of learning               ║
╚══════════════════════════════════════════════════════════════════════════════╝

WHAT IS THIS FILE?
─────────────────
This is a Python script. A script is just a text file full of instructions
that your computer follows from top to bottom, like a recipe.

WHAT DOES IT DO?
────────────────
Imagine you have a super-smart tutor friend who:
  1. You say "teach me Python decorators"
  2. They immediately Google it to get the latest info
  3. They explain it clearly with examples and analogies
  4. They quiz you at the end
  5. They write in their notebook: "remind me to quiz them again in 3 days"

That's exactly what this script does — but the "friend" is Claude (an AI).

THE FLOW (the journey of one lesson):
──────────────────────────────────────
  YOU type a topic
       │
       ▼
  Script asks Claude: "teach me this topic, search the web first"
       │
       ▼
  Claude uses its web_search tool to find the latest info online
       │
       ▼
  Claude writes a structured lesson (like a mini textbook page)
       │
       ▼
  Script displays the lesson beautifully in your terminal
       │
       ▼
  Script asks Claude to extract the quiz questions from the lesson
       │
       ▼
  YOU answer the quiz questions
       │
       ▼
  Claude grades your answers and gives feedback
       │
       ▼
  Script saves your score + schedules when to review again (SQLite database)

HOW DO SCRIPTS TALK TO AI?
───────────────────────────
Claude is a program running on Anthropic's computers (servers) far away.
To use Claude from our script, we send it messages over the internet,
just like sending a text message — except it's code talking to code.

This is called an API (Application Programming Interface).
Think of it as a waiter at a restaurant:
  - YOU are the customer (our script)
  - The WAITER is the API (takes your order, brings back food)
  - The KITCHEN is Claude (does the actual work)
  - The MENU is the API documentation (tells you what you can order)

We use the `anthropic` Python library (imported below) as our "waiter".
"""

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: IMPORTS
# What is an import?
#   Python comes with basic tools built in. But for extra tools, you need to
#   "import" them — like downloading an app on your phone before using it.
#   These tools are called "libraries" or "packages".
# ══════════════════════════════════════════════════════════════════════════════

import json      # json = JavaScript Object Notation
                 # A way to store/send structured data as text.
                 # Example: {"name": "Alice", "age": 30}
                 # We use it to send/receive data from Claude in a predictable format.

from pathlib import Path
# Path = a tool for working with file and folder locations.
# Path.home() finds your home folder regardless of whether you're on Mac/Windows/Linux.

# Import shared code from core.py — the database functions and system prompt
# live there so both agent.py (terminal) and streamlit_app.py (web) can use them
# without either one pulling in the other's dependencies.
from core import (
    DB_PATH,
    LESSON_SYSTEM_PROMPT,
    get_due_reviews,
    init_db,
    save_progress,
)

import anthropic
# THIS IS THE MAIN TOOL. The `anthropic` library is what lets us talk to Claude.
# When you did `pip install anthropic`, Python downloaded this library.
# It handles all the internet communication, authentication, and message formatting for us.

from rich.console import Console   # Console = the "printer" that outputs beautiful text
from rich.markdown import Markdown  # Markdown = converts **bold**, ## headers etc. to colors
from rich.panel import Panel        # Panel = draws a box around text
from rich.prompt import Confirm, Prompt  # Prompt = asks user to type something
                                         # Confirm = asks user yes/no
from rich.rule import Rule          # Rule = draws a horizontal line ──────────────
from rich.theme import Theme        # Theme = defines color names (like CSS for terminal)

# `rich` is a library that makes terminal output beautiful.
# Without it, everything would just be plain white text.
# With it, we get colors, boxes, formatted markdown, spinners, etc.


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: VISUAL THEME (Colors & Styles)
# ══════════════════════════════════════════════════════════════════════════════

# A Theme is like a color palette. We give names to colors so we can use
# them consistently throughout the script.
# Instead of remembering "use bold cyan for info messages", we just say [info].
theme = Theme({
    "info":    "bold cyan",     # Bright blue — for informational messages
    "success": "bold green",    # Green — for things that went well
    "warning": "bold yellow",   # Yellow — for cautions or things to pay attention to
    "error":   "bold red",      # Red — for mistakes or failures
    "topic":   "bold magenta",  # Purple — for topic names (stands out)
    "section": "bold blue",     # Blue — for section headers
})

# Create a Console object — this is our "printer" for the terminal.
# All output goes through this object so it applies our theme.
console = Console(theme=theme)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: DATABASE SETUP (SQLite — Your Learning Diary)
#
# WHAT IS A DATABASE?
#   Imagine a very organized filing cabinet.
#   Each "drawer" is a table. Each "folder" is a row. Each "label" is a column.
#
# WHY DO WE NEED IT?
#   When the script closes, all variables disappear. To remember your progress
#   between sessions, we need to save data somewhere permanent — a database file.
#
# OUR DATABASE HAS ONE TABLE: learned_topics
#   ┌──────┬───────────────┬─────────────────────┬─────────────────────┬──────────────┬────────────┐
#   │  id  │     topic     │     learned_at      │     next_review     │ review_count │ quiz_score │
#   ├──────┼───────────────┼─────────────────────┼─────────────────────┼──────────────┼────────────┤
#   │   1  │ decorators    │ 2025-01-15 10:30:00 │ 2025-01-16 10:30:00 │      0       │    0.85    │
#   │   2  │ async/await   │ 2025-01-15 11:00:00 │ 2025-01-18 11:00:00 │      1       │    0.70    │
#   └──────┴───────────────┴─────────────────────┴─────────────────────┴──────────────┴────────────┘
# ══════════════════════════════════════════════════════════════════════════════

# Where to save the database file.
# Path.home() = your home directory (e.g. /home/michael or C:\Users\michael)
# The / operator joins path pieces (like os.path.join but cleaner)
# Result example: /home/michael/.learning_agent/progress.db
DB_PATH = Path.home() / ".learning_agent" / "progress.db"


def init_db():
    """
    WHAT THIS FUNCTION DOES:
    Creates the database file and table if they don't exist yet.
    Like setting up a brand new filing cabinet on your first day.

    A "function" is a named set of instructions you can run by calling its name.
    Think of it like a named recipe: "to make pancakes, do these steps..."
    """

    # Create the folder if it doesn't exist yet.
    # exist_ok=True means "don't crash if the folder already exists"
    DB_PATH.parent.mkdir(exist_ok=True)

    # sqlite3.connect() opens (or creates) the database file.
    # Think of it as opening the filing cabinet.
    # `conn` is short for "connection" — our handle to the database.
    conn = sqlite3.connect(DB_PATH)

    # conn.execute() runs an SQL command.
    # SQL (Structured Query Language) is the language databases speak.
    # This command says: "Create a table called learned_topics with these columns,
    # but only if it doesn't already exist."
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learned_topics (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            topic        TEXT NOT NULL,
            learned_at   TEXT NOT NULL,
            next_review  TEXT NOT NULL,
            review_count INTEGER DEFAULT 0,
            quiz_score   REAL DEFAULT 0.0
        )
    """)
    # SQL explanation:
    # CREATE TABLE IF NOT EXISTS → only create if it's not already there
    # id INTEGER PRIMARY KEY AUTOINCREMENT → auto-numbering ID (1, 2, 3...)
    # topic TEXT NOT NULL → a text field that must have a value
    # learned_at TEXT NOT NULL → we store dates as text (ISO format)
    # next_review TEXT NOT NULL → when to review this topic again
    # review_count INTEGER DEFAULT 0 → starts at 0, counts how many times reviewed
    # quiz_score REAL DEFAULT 0.0 → a decimal number (0.0 to 1.0), starts at 0

    # conn.commit() saves the changes permanently.
    # Like pressing Ctrl+S after typing in a document.
    conn.commit()

    # Return the connection so the caller can use it.
    return conn


def save_progress(topic: str, quiz_score: float):
    """
    WHAT THIS FUNCTION DOES:
    Saves your quiz result and schedules the next review using spaced repetition.

    WHAT IS SPACED REPETITION?
    It's based on research by Hermann Ebbinghaus (1885) who discovered the
    "forgetting curve" — our memory fades exponentially over time.
    The KEY insight: reviewing just before you forget something makes the memory
    much stronger and lasts much longer.

    The optimal schedule is: 1 day → 3 days → 7 days → 14 days → 30 days → 60 days
    After each review, the memory is stronger, so you can wait longer before the next.

    WHAT ARE "TYPE HINTS" (the : str and : float)?
    They tell you what kind of data the function expects.
      topic: str   → topic should be a string (text), e.g. "Python decorators"
      quiz_score: float → score should be a decimal, e.g. 0.85 (meaning 85%)
    Python doesn't enforce these, but they help you understand the code.
    """

    # Open the database
    conn = init_db()

    # CHECK: Have we studied this topic before?
    # ? is a placeholder — sqlite fills it in safely (prevents SQL injection attacks)
    # .fetchone() gets the first matching row, or None if nothing found
    row = conn.execute(
        "SELECT id, review_count FROM learned_topics WHERE topic = ?",
        (topic.lower(),)   # .lower() makes comparison case-insensitive
                           # "Decorators" and "decorators" are treated the same
    ).fetchone()

    # The spaced repetition schedule: how many days to wait before each review.
    # Index 0 = first time studying → review in 1 day
    # Index 1 = second time → review in 3 days
    # Index 2 = third time → review in 7 days
    # ... and so on
    intervals = [1, 3, 7, 14, 30, 60]  # days between reviews (Ebbinghaus curve)

    # Get the current date and time
    now = datetime.now()

    if row:
        # ── Topic EXISTS in database: UPDATE it ──────────────────────────────
        # Unpack the row into two variables
        # row is a tuple like (1, 3) → topic_id=1, review_count=3
        topic_id, review_count = row

        # Pick the next interval using the UPCOMING review_count (after this save).
        # The DB still holds the OLD count — we haven't incremented it yet.
        # So we use review_count + 1 to look up the right spacing.
        #
        # Example progression:
        #   review_count in DB = 0 → upcoming count = 1 → intervals[1] = 3 days
        #   review_count in DB = 1 → upcoming count = 2 → intervals[2] = 7 days
        #   review_count in DB = 5 → upcoming count = 6 → clamped to intervals[5] = 60 days
        #
        # min() prevents going out of bounds if count exceeds the list length.
        next_interval = intervals[min(review_count + 1, len(intervals) - 1)]

        # Calculate when the next review should happen
        next_review = now + timedelta(days=next_interval)

        # UPDATE the existing row in the database
        conn.execute(
            """UPDATE learned_topics
               SET learned_at=?, next_review=?, review_count=review_count+1, quiz_score=?
               WHERE id=?""",
            (now.isoformat(), next_review.isoformat(), quiz_score, topic_id),
            # .isoformat() converts datetime to a standard text format
            # Example: "2025-01-15T10:30:00.123456"
        )
    else:
        # ── Topic is NEW: INSERT a fresh row ─────────────────────────────────
        next_review = now + timedelta(days=1)  # First review: tomorrow
        conn.execute(
            """INSERT INTO learned_topics (topic, learned_at, next_review, quiz_score)
               VALUES (?, ?, ?, ?)""",
            (topic.lower(), now.isoformat(), next_review.isoformat(), quiz_score),
        )

    # Save changes and close the database (like saving and closing a file)
    conn.commit()
    conn.close()


def get_due_reviews() -> list[dict]:
    """
    WHAT THIS FUNCTION DOES:
    Looks in the database for topics where the review date has passed.
    Like checking your calendar for overdue appointments.

    RETURN TYPE `-> list[dict]`:
    This tells you the function returns a list of dictionaries.
    A dictionary is like a labeled box:
      {"topic": "decorators", "score": 0.85, "review_count": 2}
    A list is a collection:
      [{"topic": "decorators", ...}, {"topic": "async/await", ...}]
    """

    conn = init_db()

    # Get current time as a text string (ISO format) for comparison
    now = datetime.now().isoformat()

    # SQL: SELECT rows WHERE next_review is in the past (≤ now)
    # ORDER BY next_review → most overdue topics first
    rows = conn.execute(
        """SELECT topic, next_review, review_count, quiz_score
           FROM learned_topics WHERE next_review <= ?
           ORDER BY next_review""",
        (now,),
    ).fetchall()   # .fetchall() gets ALL matching rows (not just the first one)

    conn.close()

    # Convert each row (a tuple) into a dictionary with named keys.
    # r[0] = topic, r[1] = next_review, r[2] = review_count, r[3] = quiz_score
    # This is called a "list comprehension" — a compact way to build a list.
    # It's equivalent to:
    #   result = []
    #   for r in rows:
    #       result.append({"topic": r[0], ...})
    #   return result
    return [
        {"topic": r[0], "next_review": r[1], "review_count": r[2], "score": r[3]}
        for r in rows
    ]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: THE SYSTEM PROMPT (Claude's Instructions)
#
# WHAT IS A SYSTEM PROMPT?
#   When you talk to Claude normally, you just send messages.
#   But a "system prompt" is like a secret set of instructions you give Claude
#   BEFORE the conversation starts.
#
#   Think of it like briefing a new employee:
#     "You are a tutor. Always explain things simply. Always give examples.
#      Always end with a quiz. Here is the exact format to follow..."
#
#   Claude will follow these instructions for the entire conversation.
#   The user never sees the system prompt — only its effects.
#
# WHY IS IT A CONSTANT (ALL_CAPS)?
#   In Python, variables named in ALL_CAPS are conventionally "constants" —
#   values that don't change while the program runs. It's just a naming
#   convention (Python doesn't actually enforce this).
#
# WHY USE """ (TRIPLE QUOTES)?
#   Triple quotes let you write text that spans multiple lines.
#   Single/double quotes only work on one line.
# ══════════════════════════════════════════════════════════════════════════════

LESSON_SYSTEM_PROMPT = """You are an expert programming tutor who teaches using the science of learning.
Your lessons are fun, clear, and memorable. You use the latest information from the web.

When teaching a topic, ALWAYS structure your lesson exactly like this:

---

## 🎯 Why This Matters
(1-2 sentences on why a programmer needs to know this — make it real and motivating)

## 🗺️ The Big Picture
(Feynman Technique: explain it in simple terms, like explaining to a smart friend who is new to programming. No jargon yet. 2-3 sentences max.)

## 🧩 Core Concepts (Chunked)
Break the topic into exactly 3-5 key concepts. For each one:
- **Concept name**: One sentence explanation
- A tiny code snippet if relevant

## 💡 The "Aha" Moment
The single most important insight that makes everything click. The mental model.
Use an analogy to something from everyday life.

## 🔥 Real Example
A practical, working code example showing the concept in action.
Keep it short (under 20 lines). Add inline comments explaining the "why", not just the "what".

## ⚡ Common Mistakes
2-3 mistakes beginners make with this topic. Keep it brief.

## 🧠 Quick Quiz (Active Recall)
Generate EXACTLY 3 quiz questions to test understanding. Format them as:

**Q1:** [question]
**A1:** [answer — hidden, only reveal if asked]

**Q2:** [question]
**A2:** [answer — hidden, only reveal if asked]

**Q3:** [question]
**A3:** [answer — hidden, only reveal if asked]

## 🚀 What to Learn Next
2-3 related topics that naturally follow this one (for interleaving).

---

Rules:
- Use emojis sparingly but effectively to make sections memorable
- Always search the web first to get the LATEST information and best practices
- If teaching a programming language feature, always note which version introduced it
- Make the tone warm, encouraging, and slightly playful — learning should be fun
- Code examples must be correct and runnable
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: THE MAIN TEACHING FUNCTION
#
# WHAT IS AN "AGENTIC LOOP"?
#   Normal AI usage: You ask → AI answers. Done. (One round trip.)
#
#   Agentic usage: You ask → AI thinks → AI uses a tool (e.g. web search) →
#                  Tool returns results → AI thinks more → AI uses another tool →
#                  ... → AI gives final answer.
#
#   This is called "agentic" because the AI acts like an AGENT — it takes
#   multiple actions to complete a goal, just like a human would.
#
#   The "loop" part: our code keeps sending messages back and forth until
#   Claude says "I'm done" (stop_reason == "end_turn").
#
# VISUAL DIAGRAM OF THE LOOP:
#
#   Our script                           Claude (on Anthropic's servers)
#       │                                        │
#       │── "Teach me Python decorators" ──────►│
#       │                                        │ (Claude decides to search web)
#       │◄── "I want to use web_search" ─────────│
#       │                                        │
#       │── "Here's the search result" ─────────►│
#       │                                        │ (Claude reads results, writes lesson)
#       │◄── "Here is your lesson: ..." ──────────│
#       │                                        │
#     DONE (stop_reason == "end_turn")
# ══════════════════════════════════════════════════════════════════════════════

def teach_topic(topic: str) -> str:
    """
    WHAT THIS FUNCTION DOES:
    Runs the full teaching sequence for a given topic.
    Returns the complete lesson text as a string.

    PARAMETER: topic: str
      The programming topic to teach, e.g. "Python decorators"

    RETURNS: str
      The full lesson text (markdown formatted)
    """

    # ── Step 1: Create the Anthropic client ──────────────────────────────────
    # This creates our "phone" to call Claude with.
    # It automatically reads your ANTHROPIC_API_KEY from environment variables.
    # An environment variable is like a global setting for your terminal session.
    # You set it with: export ANTHROPIC_API_KEY="sk-ant-..."
    client = anthropic.Anthropic()

    # Show the user we're starting (using our themed console)
    console.print(
        f"\n[info]Searching the web and preparing your lesson on:[/info] "
        f"[topic]{topic}[/topic]\n"
    )

    # ── Step 2: Define what TOOLS Claude can use ──────────────────────────────
    # Tools are special capabilities we give Claude beyond just talking.
    # Without tools, Claude only knows what was in its training data (which has a cutoff date).
    # With web_search, Claude can look things up RIGHT NOW.
    #
    # "web_search_20260209" is the tool type — the "20260209" is a version date.
    # "web_search" is what Claude calls this tool in conversation.
    # This is a "server-side tool" — Anthropic's servers run the actual web search.
    # We don't need to write any search code ourselves!
    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
    ]

    # ── Step 3: Build the initial message ────────────────────────────────────
    # The Claude API expects messages in a specific format:
    # A list of dicts, each with "role" and "content".
    #
    # "role" can be:
    #   "user"      → messages from the human (us, in this case)
    #   "assistant" → messages from Claude
    #
    # Think of it like a chat log:
    #   [
    #     {"role": "user",      "content": "What's 2+2?"},
    #     {"role": "assistant", "content": "It's 4."},
    #     {"role": "user",      "content": "What about 3+3?"},
    #   ]
    #
    # We send the whole conversation history every time (the API is stateless —
    # it doesn't remember previous requests).
    messages = [
        {
            "role": "user",
            "content": (
                f"Teach me about: **{topic}**\n\n"
                f"Search the web first to get the latest information, best practices, "
                f"and any recent changes. Then deliver a lesson following the exact "
                f"structure in your instructions. Make it fun and memorable!"
                # The f"..." syntax is an "f-string" (formatted string).
                # It lets you embed variables directly in text using {variable_name}.
                # f"Hello {topic}" with topic="Python" becomes "Hello Python"
            ),
        }
    ]

    # ── Step 4: The Agentic Loop ──────────────────────────────────────────────
    # This is where the magic happens.
    # We keep sending messages to Claude until it says "I'm done" (end_turn).
    # In between, Claude might search the web once or multiple times.

    full_response = ""   # We'll collect the lesson text here
    iteration = 0        # Count how many times we've looped
    max_iterations = 10  # Safety limit: stop after 10 loops no matter what
                         # (prevents infinite loops if something goes wrong)

    # console.status() shows a spinning animation while we wait.
    # The `with` keyword ensures it stops spinning when we're done.
    # This is called a "context manager" — it handles setup and cleanup automatically.
    with console.status("[bold cyan]Claude is searching and thinking...[/bold cyan]"):

        while iteration < max_iterations:
            # while loop: keep running the indented code as long as the condition is True
            # When iteration reaches max_iterations, the condition becomes False and we stop.

            iteration += 1   # iteration += 1 is shorthand for iteration = iteration + 1

            # ── Send a request to Claude ──────────────────────────────────────
            # client.messages.create() is the main API call.
            # It sends our messages to Claude and waits for a response.
            # This involves:
            #   1. Building an HTTP request
            #   2. Sending it over the internet to Anthropic's servers
            #   3. Waiting for Claude to process it
            #   4. Receiving the response
            # The `anthropic` library handles all of this for us.
            response = client.messages.create(
                model="claude-sonnet-4-6",
                # Sonnet: 85% of Opus quality at 1/3 the price — ideal for lessons.

                max_tokens=8000,
                # Maximum length of Claude's response.
                # A "token" is roughly 3/4 of a word.
                # 8000 tokens ≈ about 6000 words — plenty for a lesson.
                # If we set this too low, Claude's response gets cut off mid-sentence.

                thinking={"type": "adaptive"},
                # This enables Claude's internal "thinking" before responding.
                # Like asking someone "take a moment to think before answering."
                # "adaptive" means Claude decides HOW MUCH to think based on complexity.
                # This produces higher quality lessons.

                system=LESSON_SYSTEM_PROMPT,
                # The system prompt we defined above — Claude's "briefing".
                # Sent with every request to keep Claude in "tutor mode".

                tools=tools,
                # The list of tools Claude can use (web_search in our case).
                # Claude can CHOOSE to use these or not.

                messages=messages,
                # The conversation history so far.
                # Grows with each loop iteration.
            )

            # ── Collect any text Claude returned ─────────────────────────────
            # response.content is a list of "blocks" — different types of content.
            # Types we might see with server-side web search:
            #   - "text" blocks: the actual lesson text we want
            #   - "thinking" blocks: Claude's internal reasoning (hidden from user)
            #   - "server_tool_use" blocks: record of the web search Claude ran
            #   - "web_search_tool_result" blocks: the search results (used internally)
            #
            # We collect ONLY "text" blocks into full_response.
            # Checking block.type == "text" is more reliable than hasattr(block, "text")
            # because some non-text blocks may also have a .text attribute.
            for block in response.content:
                if block.type == "text":
                    full_response += block.text  # += appends to the string

            # ── Check WHY Claude stopped ──────────────────────────────────────
            # response.stop_reason tells us why Claude stopped generating.
            #
            # IMPORTANT: web_search_20260209 is a SERVER-SIDE tool.
            # This means Anthropic's servers execute the web search automatically
            # as part of Claude's response — we never see stop_reason="tool_use".
            # The two stop reasons we actually need to handle are:
            #
            #   "end_turn"   → Claude finished everything naturally. We're done.
            #   "pause_turn" → The server-side tool loop hit its iteration limit
            #                  (max ~10 web searches per turn). We re-send the
            #                  conversation and Claude picks up where it left off.

            if response.stop_reason == "end_turn":
                # ✅ Claude finished the lesson. Break out of the while loop.
                break

            if response.stop_reason == "pause_turn":
                # ⏸ Server hit the tool-loop limit mid-lesson.
                # Append Claude's partial response to the history and loop again.
                # Claude will resume automatically — do NOT add a new user message.
                messages.append({"role": "assistant", "content": response.content})
                continue  # `continue` jumps to the next while-loop iteration

    # After the loop, full_response contains the complete lesson text.
    return full_response


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: THE QUIZ FUNCTION
#
# WHY QUIZ AT ALL?
#   Research by Henry Roediger III (2006) showed that being TESTED on material
#   improves memory far more than re-reading it. This is called the
#   "Testing Effect" or "Retrieval Practice."
#
#   Re-reading feels easier, so our brain tricks us into thinking we know it.
#   Testing forces us to RETRIEVE the knowledge, which strengthens the memory trace.
#
# HOW THIS FUNCTION WORKS:
#   1. Send the lesson to Claude → ask it to extract the 3 quiz questions as JSON
#   2. Show the questions to the user one at a time
#   3. Collect the user's answers
#   4. Send the lesson + questions + answers back to Claude → ask for grading
#   5. Display the feedback
#   6. Ask Claude to give a numeric score (0.0 to 1.0)
#   7. Return the score (so we can save it)
# ══════════════════════════════════════════════════════════════════════════════

def run_quiz(lesson_text: str) -> float:
    """
    WHAT THIS FUNCTION DOES:
    Extracts quiz questions from the lesson, runs them interactively,
    grades the answers, and returns a score from 0.0 to 1.0.

    PARAMETER: lesson_text: str
      The complete lesson text (so Claude can extract questions and grade answers)

    RETURNS: float
      Score between 0.0 (0%) and 1.0 (100%)
    """

    # Create a fresh Anthropic client
    # (We could reuse the one from teach_topic, but keeping it local is cleaner)
    client = anthropic.Anthropic()

    # Print a visual separator and instructions
    console.print(Rule("[bold yellow]🧠 Time to Test Your Understanding![/bold yellow]"))
    # Rule() draws a horizontal line: ─────── Title ───────

    console.print("\n[warning]Answer these questions from memory — don't scroll up![/warning]\n")

    # ── Step 1: Extract quiz questions from the lesson ────────────────────────
    # We ask Claude to read the lesson it just wrote and pull out
    # the 3 quiz questions in a structured JSON format.
    #
    # WHY JSON FORMAT?
    #   If we just asked "list the questions", Claude might format them differently
    #   each time (numbered lists, bullet points, etc.), making them hard to parse.
    #   JSON gives us a predictable structure we can reliably extract from.
    #
    # WHAT IS output_config?
    #   This tells Claude: "Your response MUST follow this exact structure."
    #   It's called "structured output" — like filling out a form instead of
    #   writing a free-form essay.
    quiz_extraction = client.messages.create(
        model="claude-haiku-4-5",  # Haiku: simple extraction, 10x cheaper
        max_tokens=1000,    # Questions are short, don't need much space
        messages=[
            {
                "role": "user",
                "content": (
                    f"From this lesson, extract ONLY the 3 quiz questions (no answers).\n\n"
                    f"Lesson:\n{lesson_text}"
                ),
            }
        ],
        output_config={
            # "format" tells Claude to return structured JSON.
            # This is based on JSON Schema — a standard way to describe JSON structure.
            "format": {
                "type": "json_schema",
                "schema": {
                    # The top-level response is an object (dictionary)
                    "type": "object",
                    "properties": {
                        # It has one key called "questions"
                        "questions": {
                            "type": "array",   # which is a list
                            "items": {
                                "type": "object",   # each item is a dict
                                "properties": {
                                    "q": {"type": "string"}  # with a "q" key (the question text)
                                },
                                "required": ["q"],
                                "additionalProperties": False,  # no extra keys allowed
                            },
                        }
                    },
                    "required": ["questions"],
                    "additionalProperties": False,
                },
            }
        },
    )

    # ── Step 2: Parse Claude's JSON response ──────────────────────────────────
    # Claude returned JSON text. We need to convert it from text to a Python dict.
    # json.loads() = "JSON load string" → turns JSON text into Python objects
    # Example: '{"questions": [{"q": "What is..."}]}' → {"questions": [{"q": "What is..."}]}
    try:
        # .content[0].text = get the text from the first content block
        quiz_data = json.loads(quiz_extraction.content[0].text)
        questions = quiz_data.get("questions", [])
        # .get("questions", []) = get the "questions" key, default to empty list
        # if the key doesn't exist (safer than quiz_data["questions"])
    except (json.JSONDecodeError, IndexError, AttributeError):
        # These errors can happen if:
        # - json.JSONDecodeError: the text isn't valid JSON
        # - IndexError: content list is empty (content[0] fails)
        # - AttributeError: content block doesn't have .text
        # Instead of crashing, we gracefully skip the quiz.
        console.print("[warning]Skipping quiz (couldn't parse questions).[/warning]")
        return 1.0  # Return perfect score so we don't punish the user for our bug

    if not questions:
        # `not questions` is True when the list is empty []
        # If no questions were extracted, skip the quiz
        return 1.0

    # ── Step 3: Ask the user the questions ───────────────────────────────────
    user_answers = []  # We'll store the user's answers here

    for i, q in enumerate(questions, 1):
        # enumerate(questions, 1) loops through the list and gives us both
        # the index (i, starting at 1) and the item (q, the question dict)
        # i=1, q={"q": "What is..."} on first iteration
        # i=2, q={"q": "How do you..."} on second iteration
        # etc.

        # Display the question with its number
        console.print(f"[bold cyan]Q{i}:[/bold cyan] {q['q']}")

        # Prompt.ask() displays a prompt and waits for the user to type something
        # and press Enter. Returns the text they typed as a string.
        answer = Prompt.ask("[bold]Your answer[/bold]")
        user_answers.append(answer)   # Add their answer to our list
        console.print()               # Print a blank line for spacing

    # ── Step 4: Have Claude grade the answers ─────────────────────────────────
    # We build one big message that contains:
    #   - The original lesson (so Claude knows the correct answers)
    #   - Each question paired with the user's answer
    # Then we ask Claude to grade each one and give feedback.

    # This builds the questions+answers section of the prompt.
    # chr(10) = the newline character (\n) — we use chr() because f-strings
    # can't contain backslashes directly inside {}.
    qa_pairs = chr(10).join(
        f"Q{i+1}: {q['q']}\nUser answer: {user_answers[i]}"
        for i, q in enumerate(questions)
    )

    with console.status("[bold cyan]Evaluating your answers...[/bold cyan]"):
        evaluation = client.messages.create(
            model="claude-haiku-4-5",  # Haiku: grading is straightforward
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"You are evaluating quiz answers for this lesson:\n\n"
                        f"{lesson_text}\n\n"
                        f"Questions and user answers:\n{qa_pairs}\n\n"
                        f"For each answer:\n"
                        f"1. Say if it's correct/partially correct/incorrect\n"
                        f"2. Give the correct answer briefly\n"
                        f"3. Give an encouraging comment\n\n"
                        f"Be kind and educational. Format as clear text, not JSON."
                    ),
                }
            ],
        )

    # Extract the feedback text from Claude's response
    feedback = evaluation.content[0].text

    # ── Step 5: Display the feedback ─────────────────────────────────────────
    console.print(Rule("[bold green]Quiz Results[/bold green]"))
    # Markdown() renders the text with formatting (bold, headers, etc.)
    console.print(Markdown(feedback))

    # ── Step 6: Get a numeric score ───────────────────────────────────────────
    # We ask Claude to read its own feedback and give a number.
    # This is simpler than trying to parse the feedback text ourselves.
    score_response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=10,   # We only need a short number like "0.8"
        messages=[
            {
                "role": "user",
                "content": (
                    f"Based on these quiz answers, give a score from 0.0 to 1.0. "
                    f"Reply with ONLY the number, nothing else.\n\n{feedback}"
                ),
            }
        ],
    )

    # Convert Claude's text response to a Python float (decimal number)
    try:
        score = float(score_response.content[0].text.strip())
        # .strip() removes any leading/trailing whitespace
        # float() converts "0.85" to 0.85
        score = max(0.0, min(1.0, score))
        # Clamp to valid range: max(0.0, ...) ensures it's not negative
        #                       min(1.0, ...) ensures it's not above 1.0
    except ValueError:
        # ValueError happens if float("abc") — the text isn't a number
        score = 0.7   # Reasonable default: assume they did okay

    return score


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: THE MAIN FUNCTION (Where Everything Begins)
#
# WHAT IS `main()`?
#   By convention, the "entry point" of a script — the first thing that runs —
#   is put in a function called main().
#
# WHAT IS `if __name__ == "__main__":`?
#   When Python runs a file directly (e.g. `python agent.py`), it sets a
#   special variable __name__ to "__main__".
#   When Python imports a file (e.g. `import agent` from another script),
#   __name__ is set to "agent" instead.
#
#   So this check means: "Only run main() if we're running this file directly."
#   This lets other scripts import our functions WITHOUT triggering the main() execution.
#   It's a Python best practice for any script that can also be a library.
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    WHAT THIS FUNCTION DOES:
    The "director" — coordinates everything in the right order:
      1. Show welcome screen
      2. Check for due reviews
      3. Ask what topic to study
      4. Teach the topic
      5. Run the quiz
      6. Save progress
    """

    # ── Welcome Screen ────────────────────────────────────────────────────────
    # Panel.fit() creates a box that fits snugly around the text.
    # border_style="magenta" makes the box outline purple.
    console.print(Panel.fit(
        "[bold magenta]🧠 Learning Agent[/bold magenta]\n"
        "[dim]Teaches programming using the science of learning[/dim]",
        border_style="magenta",
    ))

    # ── Check for Due Reviews ─────────────────────────────────────────────────
    # Call our database function to see if any topics need reviewing today.
    due = get_due_reviews()

    if due:
        # f-string with len(due) — len() counts items in a list
        console.print(f"\n[warning]📅 You have {len(due)} topic(s) due for review:[/warning]")

        for item in due:
            # Loop through each due topic and display it
            # {item['score']:.0%} formats the score as a percentage with 0 decimal places
            # e.g. 0.85 → "85%"
            console.print(
                f"  • [topic]{item['topic']}[/topic] "
                f"(reviewed {item['review_count']}x, score: {item['score']:.0%})"
            )
        console.print()   # blank line

        # Confirm.ask() shows a yes/no prompt. Returns True if user says yes.
        # default=False means pressing Enter (without typing) counts as "No"
        if Confirm.ask("Review a due topic first?", default=False):
            topic_names = [d["topic"] for d in due]  # Extract just the topic names
            choice = Prompt.ask(
                "Which topic?",
                choices=topic_names,    # Only accept these exact choices
                default=topic_names[0], # Pre-fill with the most overdue topic
            )
            topic = choice
        else:
            # User chose to study something new
            topic = Prompt.ask("\n[bold]What topic do you want to learn?[/bold]")
    else:
        # No due reviews — just ask what to learn
        topic = Prompt.ask("\n[bold]What topic do you want to learn?[/bold]")

    # ── Validate Input ────────────────────────────────────────────────────────
    # .strip() removes whitespace from both ends of the string
    # "not topic.strip()" is True if the string is empty or only whitespace
    if not topic.strip():
        console.print("[error]No topic entered. Goodbye![/error]")
        return   # `return` in main() exits the function (and thus the program)

    # ── Teach the Topic ───────────────────────────────────────────────────────
    # Call our teach_topic() function, which does the heavy lifting.
    # This may take 30-60 seconds as Claude searches and generates the lesson.
    lesson = teach_topic(topic)

    # ── Display the Lesson ────────────────────────────────────────────────────
    # Rule() draws a nice header line
    console.print(Rule(f"[bold magenta]Lesson: {topic}[/bold magenta]"))
    # Markdown() renders the lesson with proper formatting
    # (## headers become big text, **bold** becomes bold, code blocks get highlighted, etc.)
    console.print(Markdown(lesson))

    # ── Quiz Time ─────────────────────────────────────────────────────────────
    console.print()   # blank line
    if Confirm.ask(
        "\n[bold yellow]Ready for the quiz?[/bold yellow] "
        "(Active recall boosts retention by 50%)",
        default=True   # pressing Enter = Yes (since quizzing is the point!)
    ):
        score = run_quiz(lesson)
        console.print(f"\n[success]Quiz complete! Score: {score:.0%}[/success]")

        # Give contextual feedback based on the score
        if score >= 0.8:
            console.print("[success]Excellent! Next review in 3 days. 🎉[/success]")
        elif score >= 0.5:
            console.print("[warning]Good effort! Review again tomorrow to solidify it. 📚[/warning]")
        else:
            console.print("[warning]No worries! Re-read the lesson and review again tomorrow. 💪[/warning]")

        # Save the topic and score to the database
        save_progress(topic, score)

    else:
        # User skipped the quiz — still save progress with a neutral score
        save_progress(topic, 0.7)
        console.print("[info]Lesson saved! Quiz yourself later for best retention.[/info]")

    # ── Goodbye ───────────────────────────────────────────────────────────────
    console.print(f"\n[dim]Progress saved to {DB_PATH}[/dim]")
    console.print("[bold magenta]Happy learning! 🚀[/bold magenta]\n")


# ── Entry Point ───────────────────────────────────────────────────────────────
# This is the last thing in the file.
# Python reads files top to bottom, so by the time it reaches here,
# all the functions above are already defined and ready to use.
#
# __name__ == "__main__" is True when you run: python agent.py
# It's False when another script does: import agent
#
# This pattern lets the file work both as a standalone script AND as a
# library that other scripts can import functions from.
if __name__ == "__main__":
    main()
