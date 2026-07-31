"""
core.py — Shared code used by both agent.py (terminal) and streamlit_app.py (web).

WHY DOES THIS FILE EXIST?
──────────────────────────
When streamlit_app.py imported from agent.py, it triggered all of agent.py's
startup code — including creating a Rich terminal Console object, which doesn't
work in a cloud web environment and caused the app to crash on Streamlit Cloud.

The fix: move the code that BOTH files need into this neutral file that has
no terminal-specific dependencies. Then each app imports from here instead.

WHAT'S IN HERE:
  - DB_PATH         the path to the SQLite database file
  - init_db()       creates the database/table if needed
  - save_progress() saves a quiz result + schedules next spaced review
  - get_due_reviews() finds topics overdue for review
  - LESSON_SYSTEM_PROMPT  Claude's teaching instructions
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


# ── Database path ─────────────────────────────────────────────────────────────
# On Streamlit Cloud the home directory is /home/adminuser — writable and fine.
# Locally it's /home/michael (or equivalent on Windows/Mac).
DB_PATH = Path.home() / ".learning_agent" / "progress.db"


def init_db():
    """Creates the database file and learned_topics table if they don't exist."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn.commit()
    return conn


def save_progress(topic: str, quiz_score: float):
    """
    Saves quiz result and calculates the next spaced repetition review date.

    Schedule: 1 day → 3 days → 7 days → 14 days → 30 days → 60 days
    Each time you review, the gap grows — based on Ebbinghaus's forgetting curve.
    """
    conn = init_db()

    row = conn.execute(
        "SELECT id, review_count FROM learned_topics WHERE topic = ?",
        (topic.lower(),)
    ).fetchone()

    intervals = [1, 3, 7, 14, 30, 60]  # days — Ebbinghaus spacing
    now = datetime.now()

    if row:
        topic_id, review_count = row
        # Use review_count + 1 because the DB still has the OLD count
        next_interval = intervals[min(review_count + 1, len(intervals) - 1)]
        next_review = now + timedelta(days=next_interval)
        conn.execute(
            """UPDATE learned_topics
               SET learned_at=?, next_review=?, review_count=review_count+1, quiz_score=?
               WHERE id=?""",
            (now.isoformat(), next_review.isoformat(), quiz_score, topic_id),
        )
    else:
        next_review = now + timedelta(days=1)
        conn.execute(
            """INSERT INTO learned_topics (topic, learned_at, next_review, quiz_score)
               VALUES (?, ?, ?, ?)""",
            (topic.lower(), now.isoformat(), next_review.isoformat(), quiz_score),
        )

    conn.commit()
    conn.close()


def get_due_reviews() -> list[dict]:
    """Returns topics whose next_review date has passed — due for review today."""
    conn = init_db()
    now = datetime.now().isoformat()
    rows = conn.execute(
        """SELECT topic, next_review, review_count, quiz_score
           FROM learned_topics WHERE next_review <= ?
           ORDER BY next_review""",
        (now,),
    ).fetchall()
    conn.close()
    return [
        {"topic": r[0], "next_review": r[1], "review_count": r[2], "score": r[3]}
        for r in rows
    ]


# ── System Prompt ─────────────────────────────────────────────────────────────
# Claude's teaching instructions. Sent with every API call so Claude stays
# in "tutor mode" regardless of what the user types.

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
