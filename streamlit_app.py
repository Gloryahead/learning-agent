"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 LEARNING AGENT — STREAMLIT WEB UI                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

WHAT IS THIS FILE?
──────────────────
This is the web version of the Learning Agent.
It uses Streamlit — a library that turns Python scripts into web apps.

HOW STREAMLIT WORKS (important to understand):
────────────────────────────────────────────────
Streamlit re-runs this ENTIRE script top-to-bottom every time the user
clicks a button, types something, or interacts with the page.

That means variables reset to their initial values on every run.
To "remember" things between reruns, we use st.session_state — a
special dictionary that persists across reruns, like a notepad that
survives each re-execution.

Think of it like this:
  Every button click = Python starts over from line 1
  st.session_state   = the only memory that survives

HOW THIS FILE RELATES TO agent.py:
────────────────────────────────────
We REUSE the database functions from agent.py (no point rewriting them).
We REWRITE the Claude API calls without Rich terminal styling
(Streamlit has its own way to show spinners, text, etc.).

PAGE FLOW:
──────────
  "home"    → Welcome screen, show due reviews, topic input
     ↓
  "lesson"  → Display the lesson Claude generated
     ↓
  "quiz"    → Show 3 questions, collect answers, grade them
     ↓
  "results" → Show score, feedback, save to database
     ↓ (clicking "Learn another topic" resets to "home")
"""

import json
import os

import anthropic
import streamlit as st

# Import shared code from core.py — a neutral file with no terminal dependencies.
# We used to import from agent.py but that pulled in Rich (terminal library)
# which caused a crash on Streamlit Cloud at startup.
from core import (
    LESSON_SYSTEM_PROMPT,
    DB_PATH,
    get_due_reviews,
    save_progress,
)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: PAGE CONFIGURATION
# Must be the FIRST Streamlit call in the script — Streamlit enforces this.
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="🧠 Learning Agent",
    page_icon="🧠",
    layout="centered",       # content sits in the middle (not full-width)
    initial_sidebar_state="collapsed",
)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: CUSTOM CSS
# Streamlit lets you inject raw CSS to fine-tune the look.
# st.markdown(..., unsafe_allow_html=True) renders HTML/CSS directly.
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* Make the main heading pop */
h1 { text-align: center; }

/* Style quiz answer text boxes */
.stTextArea textarea {
    background-color: #1a1a2e;
    border: 1px solid #a855f7;
    border-radius: 8px;
    font-size: 0.95rem;
}

/* Make primary buttons purple and full-width */
div.stButton > button[kind="primary"] {
    width: 100%;
    padding: 0.6rem;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    background-color: #a855f7;
    border: none;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #9333ea;
}

/* Score badge styling */
.score-badge {
    text-align: center;
    font-size: 3rem;
    font-weight: 700;
    padding: 1rem;
    border-radius: 16px;
    margin: 1rem 0;
}

/* Info boxes */
.info-box {
    background-color: #1a1a2e;
    border-left: 4px solid #a855f7;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: API CLIENT FACTORY
#
# HOW THE API KEY IS HANDLED:
# ────────────────────────────
# Locally:         Reads from .streamlit/secrets.toml
# Streamlit Cloud: Reads from the Secrets section in the dashboard
# Fallback:        Reads from the ANTHROPIC_API_KEY environment variable
#
# st.secrets works like a dictionary — st.secrets["ANTHROPIC_API_KEY"]
# If the key isn't found there, we fall back to os.environ.
# ══════════════════════════════════════════════════════════════════════════════

def get_client() -> anthropic.Anthropic:
    """
    Creates and returns an Anthropic API client.
    Tries Streamlit secrets first, then falls back to environment variable.
    """
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error(
            "❌ No API key found. Add ANTHROPIC_API_KEY to `.streamlit/secrets.toml` "
            "or set it as an environment variable."
        )
        st.stop()  # Halt execution — nothing else runs after st.stop()
    return anthropic.Anthropic(api_key=api_key)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: SESSION STATE INITIALISATION
#
# Session state is Streamlit's memory between reruns.
# We initialise every key we'll use — if it already exists, setdefault
# leaves it unchanged (so we don't wipe data on each rerun).
#
# Keys we use:
#   page        — which screen to show ("home", "lesson", "quiz", "results")
#   topic       — the topic the user wants to learn
#   lesson      — the full lesson text Claude generated
#   questions   — list of quiz question dicts [{"q": "..."}]
#   answers     — list of user's typed answers
#   feedback    — Claude's grading text
#   score       — float 0.0–1.0
# ══════════════════════════════════════════════════════════════════════════════

st.session_state.setdefault("page", "home")
st.session_state.setdefault("topic", "")
st.session_state.setdefault("lesson", "")
st.session_state.setdefault("questions", [])
st.session_state.setdefault("answers", [])
st.session_state.setdefault("feedback", "")
st.session_state.setdefault("score", 0.0)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: CORE AI FUNCTIONS (Streamlit-friendly versions)
#
# These do the same work as teach_topic() and run_quiz() in agent.py
# but without any Rich terminal output.
# ══════════════════════════════════════════════════════════════════════════════

def teach_topic(topic: str) -> str:
    """
    Calls Claude to teach a topic.
    Uses web_search to get latest info, then generates a structured lesson.
    Returns the lesson as a markdown string.

    This is an AGENTIC LOOP:
      1. Send the user's topic to Claude
      2. Claude searches the web (server-side — we don't do the searching)
      3. Claude writes the lesson
      4. We return the lesson text

    Because web_search_20260209 is server-side, Claude handles the
    search internally. We only ever see stop_reason "end_turn" (done)
    or "pause_turn" (hit the server's tool-loop limit, resume by resending).
    """
    client = get_client()

    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    messages = [
        {
            "role": "user",
            "content": (
                f"Teach me about: **{topic}**\n\n"
                "Search the web first to get the latest information, best practices, "
                "and any recent changes. Then deliver a lesson following the exact "
                "structure in your instructions. Make it fun and memorable!"
            ),
        }
    ]

    full_lesson = ""
    max_iterations = 10  # safety cap on the agentic loop

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",  # Sonnet: 85% of Opus quality at 1/3 the price
            max_tokens=8000,
            system=LESSON_SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Collect only "text" type blocks (ignore thinking, server_tool_use, etc.)
        for block in response.content:
            if block.type == "text":
                full_lesson += block.text

        if response.stop_reason == "end_turn":
            # Claude finished naturally — we're done
            break

        if response.stop_reason == "pause_turn":
            # Server-side tool hit its loop limit.
            # Append Claude's response and resend — it resumes automatically.
            messages.append({"role": "assistant", "content": response.content})
            # No extra user message needed — Claude knows to continue

    return full_lesson


def extract_questions(lesson_text: str) -> list[dict]:
    """
    Asks Claude to pull the 3 quiz questions out of the lesson.
    Uses structured output (JSON schema) so we always get a reliable format.
    Returns a list like: [{"q": "What is X?"}, {"q": "How does Y work?"}]
    """
    client = get_client()

    response = client.messages.create(
        model="claude-haiku-4-5",  # Haiku: simple extraction task, 10x cheaper
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": (
                    "From this lesson, extract ONLY the 3 quiz questions (no answers).\n\n"
                    f"Lesson:\n{lesson_text}"
                ),
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"q": {"type": "string"}},
                                "required": ["q"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["questions"],
                    "additionalProperties": False,
                },
            }
        },
    )

    try:
        data = json.loads(response.content[0].text)
        return data.get("questions", [])
    except (json.JSONDecodeError, IndexError, AttributeError):
        return []


def grade_answers(lesson_text: str, questions: list[dict], answers: list[str]) -> tuple[str, float]:
    """
    Sends the lesson + questions + user answers to Claude for grading.
    Returns (feedback_markdown: str, score: float 0.0–1.0).
    """
    client = get_client()

    # Build a readable Q&A block for Claude to evaluate
    qa_block = "\n".join(
        f"Q{i + 1}: {q['q']}\nUser's answer: {answers[i]}"
        for i, q in enumerate(questions)
    )

    # Ask Claude to grade and give feedback
    feedback_resp = client.messages.create(
        model="claude-haiku-4-5",  # Haiku: grading is straightforward, no need for Opus
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are evaluating quiz answers for this lesson:\n\n{lesson_text}\n\n"
                    f"Questions and answers:\n{qa_block}\n\n"
                    "For each answer:\n"
                    "1. Say if it's correct / partially correct / incorrect\n"
                    "2. Give the correct answer briefly\n"
                    "3. Add an encouraging comment\n\n"
                    "Be warm and educational. Format as markdown."
                ),
            }
        ],
    )
    feedback = feedback_resp.content[0].text

    # Ask Claude to turn that feedback into a single number
    score_resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=10,
        messages=[
            {
                "role": "user",
                "content": (
                    "Based on these quiz results, give a score from 0.0 to 1.0. "
                    f"Reply with ONLY the number.\n\n{feedback}"
                ),
            }
        ],
    )

    try:
        score = float(score_resp.content[0].text.strip())
        score = max(0.0, min(1.0, score))   # clamp to valid range
    except ValueError:
        score = 0.7

    return feedback, score


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: PAGE RENDERERS
#
# Each function renders one "page" of the app.
# The main() function at the bottom routes to the right one
# based on st.session_state["page"].
#
# Changing st.session_state["page"] and calling st.rerun() is how we
# navigate between pages — there's no URL routing in basic Streamlit.
# ══════════════════════════════════════════════════════════════════════════════

def page_home():
    """
    The welcome / home screen.
    Shows due reviews and a topic input box.
    """
    # ── Header ───────────────────────────────────────────────────────────────
    st.title("🧠 Learning Agent")
    st.markdown(
        "<div class='info-box'>"
        "Enter any programming topic and I'll search the web, teach it to you "
        "using the science of learning, then quiz you to make it stick."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Due Reviews ──────────────────────────────────────────────────────────
    due = get_due_reviews()
    if due:
        st.markdown("---")
        st.markdown(f"### 📅 {len(due)} Topic(s) Due for Review")
        st.caption("Your brain is about to forget these — review them now for maximum retention.")

        for item in due:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown(f"**{item['topic'].title()}**")
            col2.markdown(f"Score: {item['score']:.0%}")
            col3.markdown(f"Reviewed {item['review_count']}×")

            # Clicking this sets the topic and jumps straight to teaching
            if st.button(f"Review now →", key=f"review_{item['topic']}"):
                st.session_state.topic = item["topic"]
                st.session_state.page = "lesson"
                st.rerun()
                # st.rerun() tells Streamlit: stop here, restart the script.
                # Session state is preserved, so page="lesson" survives.

        st.markdown("---")

    # ── Topic Input ───────────────────────────────────────────────────────────
    st.markdown("### 💡 What do you want to learn today?")

    # st.text_input renders a text box. The value the user typed is returned.
    topic_input = st.text_input(
        label="Topic",
        placeholder='e.g. "Python decorators", "Docker containers", "React hooks"',
        label_visibility="collapsed",  # hide the label (placeholder text is enough)
    )

    # Suggestion chips — clicking one pre-fills the topic input
    st.caption("Or try one of these:")
    suggestions = [
        "Python decorators", "async/await", "SQL joins",
        "Docker containers", "REST API design", "React hooks",
    ]
    # Display 3 buttons per row using columns
    rows = [suggestions[i:i+3] for i in range(0, len(suggestions), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for col, suggestion in zip(cols, row):
            if col.button(suggestion, use_container_width=True):
                st.session_state.topic = suggestion
                st.session_state.page = "lesson"
                st.rerun()

    # ── Teach Button ──────────────────────────────────────────────────────────
    st.markdown("")   # spacer
    if st.button("🚀 Teach me this!", type="primary", use_container_width=True):
        if not topic_input.strip():
            st.warning("Please enter a topic first.")
        else:
            st.session_state.topic = topic_input.strip()
            st.session_state.page = "lesson"
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        f"📚 Learning history saved to `{DB_PATH}`  \n"
        "Powered by Claude claude-opus-4-6 · Spaced repetition · Active recall"
    )


def page_lesson():
    """
    Generates and displays the lesson.
    The lesson is generated ONCE (on first visit) and cached in session state.
    Subsequent reruns skip regeneration and just display the stored lesson.
    """
    topic = st.session_state.topic

    # ── Navigation breadcrumb ─────────────────────────────────────────────────
    if st.button("← Back"):
        st.session_state.page = "home"
        st.session_state.lesson = ""   # clear the cached lesson
        st.rerun()

    st.title(f"📖 {topic.title()}")

    # ── Generate lesson if we don't have one yet ──────────────────────────────
    # st.session_state.lesson is "" when we first arrive on this page.
    # Once generated, it's stored so reruns don't regenerate.
    if not st.session_state.lesson:
        with st.status("🔍 Searching the web and preparing your lesson...", expanded=True) as status:
            # st.status() shows an expandable box with a spinner.
            # `expanded=True` means it starts open so the user can see the message.
            st.write("Searching for the latest information...")
            st.write("Structuring your lesson using learning science...")
            lesson = teach_topic(topic)
            st.session_state.lesson = lesson
            status.update(label="✅ Lesson ready!", state="complete", expanded=False)
            # status.update() changes the spinner to a checkmark when done

    # ── Display the lesson ────────────────────────────────────────────────────
    # st.markdown() renders markdown text with headers, code blocks, bold, etc.
    st.markdown(st.session_state.lesson)

    # ── Quiz prompt ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div class='info-box'>"
        "🧠 <strong>Active recall</strong> — answering questions from memory — "
        "boosts retention by up to 50% compared to just re-reading."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    if col1.button("🎯 Take the quiz", type="primary", use_container_width=True):
        # Extract questions before navigating so the quiz page has them ready
        with st.spinner("Preparing quiz questions..."):
            questions = extract_questions(st.session_state.lesson)
        st.session_state.questions = questions
        st.session_state.page = "quiz"
        st.rerun()

    if col2.button("⏭ Skip quiz", use_container_width=True):
        save_progress(topic, 0.7)   # Save with neutral score
        st.session_state.page = "home"
        st.session_state.lesson = ""
        st.rerun()


def page_quiz():
    """
    Displays the 3 quiz questions and collects the user's answers.
    All questions are shown at once — the user fills them in and submits.
    This works better with Streamlit's rerun model than one-at-a-time.
    """
    topic = st.session_state.topic
    questions = st.session_state.questions

    # ── Navigation ────────────────────────────────────────────────────────────
    if st.button("← Back to lesson"):
        st.session_state.page = "lesson"
        st.rerun()

    st.title("🧠 Quick Quiz")
    st.markdown(f"**Topic:** {topic.title()}")
    st.caption("Answer from memory — don't scroll up! That's the whole point.")
    st.markdown("---")

    # Handle edge case: no questions were extracted
    if not questions:
        st.warning("Couldn't extract quiz questions from this lesson. Saving your progress...")
        save_progress(topic, 0.7)
        if st.button("← Back to home"):
            st.session_state.page = "home"
            st.session_state.lesson = ""
            st.rerun()
        return

    # ── Question inputs ───────────────────────────────────────────────────────
    # We collect answers in a local list, then save to session state on submit.
    # st.text_area() is a multi-line text box — better for answers than text_input.
    user_answers = []
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i + 1}: {q['q']}**")
        answer = st.text_area(
            label=f"answer_{i}",          # unique key for Streamlit's widget tracking
            placeholder="Type your answer here...",
            label_visibility="collapsed",
            key=f"answer_input_{i}",      # key persists the value across reruns
            height=100,
        )
        user_answers.append(answer)
        st.markdown("")   # spacer

    st.markdown("---")

    # ── Submit button ─────────────────────────────────────────────────────────
    if st.button("✅ Submit answers", type="primary", use_container_width=True):
        # Check the user filled in at least something
        if not any(a.strip() for a in user_answers):
            st.warning("Please answer at least one question before submitting.")
            return

        # Grade the answers
        with st.spinner("📝 Grading your answers..."):
            feedback, score = grade_answers(
                st.session_state.lesson, questions, user_answers
            )

        # Store results in session state and navigate to results page
        st.session_state.answers = user_answers
        st.session_state.feedback = feedback
        st.session_state.score = score
        st.session_state.page = "results"
        st.rerun()


def page_results():
    """
    Shows the quiz results: score badge, detailed feedback, and next steps.
    Also saves progress to the database.
    """
    topic = st.session_state.topic
    score = st.session_state.score
    feedback = st.session_state.feedback

    st.title("📊 Quiz Results")
    st.markdown(f"**Topic:** {topic.title()}")
    st.markdown("---")

    # ── Score badge ───────────────────────────────────────────────────────────
    # Pick colors and emoji based on score bracket
    if score >= 0.8:
        color = "#22c55e"    # green
        emoji = "🎉"
        message = "Excellent! You've got this."
        next_review = "3 days"
    elif score >= 0.5:
        color = "#f59e0b"    # amber
        emoji = "📚"
        message = "Good effort! Review again tomorrow."
        next_review = "1 day"
    else:
        color = "#a855f7"    # purple
        emoji = "💪"
        message = "Keep at it — re-read the lesson and try again tomorrow."
        next_review = "1 day"

    # Render the score as a big coloured number
    st.markdown(
        f"<div class='score-badge' style='background-color:{color}22; color:{color}; "
        f"border: 2px solid {color};'>"
        f"{emoji} {score:.0%}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # st.metric() shows a large KPI-style number with a label
    col1, col2 = st.columns(2)
    col1.metric("Your Score", f"{score:.0%}")
    col2.metric("Next Review", next_review)

    st.info(f"**{message}**")

    # ── Detailed feedback ─────────────────────────────────────────────────────
    st.markdown("### 📝 Answer Feedback")
    st.markdown(feedback)

    # ── Save to database ──────────────────────────────────────────────────────
    # We only save once — check a flag in session state to avoid double-saving
    # on reruns (Streamlit reruns the whole script, so without this guard
    # it would save every time the page renders).
    if not st.session_state.get("progress_saved"):
        save_progress(topic, score)
        st.session_state.progress_saved = True

    # ── Actions ───────────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)

    if col1.button("🔄 Re-read lesson", use_container_width=True):
        st.session_state.page = "lesson"
        st.rerun()

    if col2.button("🚀 Learn another topic", type="primary", use_container_width=True):
        # Reset all session state for the next topic
        for key in ["topic", "lesson", "questions", "answers", "feedback", "progress_saved"]:
            st.session_state[key] = "" if isinstance(st.session_state.get(key), str) else []
        st.session_state.score = 0.0
        st.session_state.progress_saved = False
        st.session_state.page = "home"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MAIN ROUTER
#
# This is the "traffic cop" — it reads the current page from session state
# and calls the right page function.
#
# Because Streamlit reruns the whole script on each interaction,
# this routing logic runs every single time.
# ══════════════════════════════════════════════════════════════════════════════

def main():
    page = st.session_state.page

    if page == "home":
        page_home()
    elif page == "lesson":
        page_lesson()
    elif page == "quiz":
        page_quiz()
    elif page == "results":
        page_results()
    else:
        # Fallback: unknown page → go home
        st.session_state.page = "home"
        st.rerun()


# Standard Python entry point
if __name__ == "__main__":
    main()
