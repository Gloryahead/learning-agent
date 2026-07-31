"""
supabase_db.py — Cloud database functions for the Streamlit web app.

WHY THIS FILE EXISTS:
─────────────────────
Streamlit Cloud resets its filesystem on every restart, so SQLite data is lost.
This file replaces the SQLite functions (from core.py) with Supabase equivalents
that store data permanently in a cloud Postgres database.

The terminal app (agent.py) still uses core.py + SQLite — it runs locally
where SQLite data persists just fine.

WHAT'S IN HERE:
  - get_supabase_client()  creates a Supabase connection using secrets
  - save_progress()        saves/updates a topic with quiz score + lesson text
  - get_due_reviews()      returns topics overdue for spaced repetition review
  - get_all_topics()       returns every saved topic for the library page
"""

from datetime import datetime, timedelta

import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """
    Creates a Supabase client using credentials stored in Streamlit secrets.
    On Streamlit Cloud: secrets come from the dashboard (Settings → Secrets).
    Locally: secrets come from .streamlit/secrets.toml.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def save_progress(topic: str, quiz_score: float, lesson_text: str = ""):
    """
    Saves quiz result, lesson text, and calculates the next spaced repetition date.

    Schedule: 1 day → 3 days → 7 days → 14 days → 30 days → 60 days

    If the topic already exists, updates it (increments review_count, updates score).
    If it's new, inserts a fresh row.
    """
    supabase = get_supabase_client()
    intervals = [1, 3, 7, 14, 30, 60]
    now = datetime.now()

    # Check if we've seen this topic before
    result = supabase.table("learned_topics") \
        .select("id, review_count") \
        .eq("topic", topic.lower()) \
        .execute()

    if result.data:
        # Topic exists — update it
        review_count = result.data[0]["review_count"]
        next_interval = intervals[min(review_count + 1, len(intervals) - 1)]
        next_review = (now + timedelta(days=next_interval)).isoformat()

        supabase.table("learned_topics").update({
            "learned_at":    now.isoformat(),
            "next_review":   next_review,
            "review_count":  review_count + 1,
            "quiz_score":    quiz_score,
            "lesson_text":   lesson_text,
        }).eq("topic", topic.lower()).execute()
    else:
        # New topic — insert it
        next_review = (now + timedelta(days=1)).isoformat()

        supabase.table("learned_topics").insert({
            "topic":        topic.lower(),
            "learned_at":   now.isoformat(),
            "next_review":  next_review,
            "review_count": 0,
            "quiz_score":   quiz_score,
            "lesson_text":  lesson_text,
        }).execute()


def get_due_reviews() -> list[dict]:
    """Returns topics whose next_review date has passed — due for review today."""
    supabase = get_supabase_client()
    now = datetime.now().isoformat()

    result = supabase.table("learned_topics") \
        .select("topic, next_review, review_count, quiz_score") \
        .lte("next_review", now) \
        .order("next_review") \
        .execute()

    return [
        {
            "topic":        r["topic"],
            "next_review":  r["next_review"],
            "review_count": r["review_count"],
            "score":        r["quiz_score"],
        }
        for r in result.data
    ]


def get_all_topics() -> list[dict]:
    """Returns every saved topic, newest first — for the library page."""
    supabase = get_supabase_client()

    result = supabase.table("learned_topics") \
        .select("topic, learned_at, next_review, review_count, quiz_score, lesson_text") \
        .order("learned_at", desc=True) \
        .execute()

    return [
        {
            "topic":        r["topic"],
            "learned_at":   r["learned_at"],
            "next_review":  r["next_review"],
            "review_count": r["review_count"],
            "score":        r["quiz_score"],
            "lesson_text":  r["lesson_text"],
        }
        for r in result.data
    ]
