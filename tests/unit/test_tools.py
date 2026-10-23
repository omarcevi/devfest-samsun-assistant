"""Unit tests for the agent's tools. No network, no Gemini."""

from app import tools
from app.tools import get_session, search_sessions, submit_feedback

SAT, SUN = "2026-10-24", "2026-10-25"


def ids(results: list[dict]) -> list[str]:
    return [r["id"] for r in results]


def test_search_by_tag():
    assert ids(search_sessions("flutter", SUN)) == ["sun-1415-kat2"]


def test_search_matches_any_word_in_title_or_tags():
    assert ids(search_sessions("AI agents", SAT)) == ["sat-1030-kat1", "sat-1130-kat1"]


def test_search_empty_topic_returns_whole_day():
    assert len(search_sessions("", SAT)) == 7
    assert len(search_sessions("", SUN)) == 10


def test_search_after_filter():
    assert ids(search_sessions("", SAT, after="14:00")) == ["sat-1415-kat1", "sat-1530-kat1", "sat-1630-kat1"]
    assert ids(search_sessions("ai", SAT, after="12:00")) == []


def test_search_unknown_day_or_topic():
    assert search_sessions("ai", "2026-10-26") == []
    assert search_sessions("kotlin", SUN) == []


def test_search_results_carry_speaker_time_and_floor():
    result = search_sessions("yolo", SUN)[0]
    assert result == {"id": "sun-1530-kat1", "title": result["title"], "speaker": "Onuralp Sezer",
                      "start": "15:30", "floor": "Kat 1"}


def test_get_session_details():
    session = get_session("sat-1030-kat1")
    assert session["speaker"] == "Omar Elcircevi"
    assert (session["day"], session["start"], session["end"], session["floor"]) == (SAT, "10:30", "11:10", "Kat 1")


def test_get_session_unknown_id():
    assert "error" in get_session("nope")


def test_submit_feedback_valid():
    tools.FEEDBACK.clear()
    assert submit_feedback("sat-1030-kat1", 5)["status"] == "saved"
    assert tools.FEEDBACK == {"sat-1030-kat1": [5]}


def test_submit_feedback_rejects_bad_input():
    assert "error" in submit_feedback("sat-1030-kat1", 0)
    assert "error" in submit_feedback("sat-1030-kat1", 6)
    assert "error" in submit_feedback("nope", 3)


def test_agenda_rules():
    """The agenda is real data: online/workshop formats match the title prefixes, no Saturday Kat 2."""
    for s in tools.SESSIONS:
        assert s["format"] == ("online" if s["title"].startswith("[Çevrimiçi]") else
                               "workshop" if s["title"].startswith("[Workshop]") else "talk")
        assert s["tags"], s["id"]
    assert not [s for s in tools.SESSIONS if s["day"] == SAT and s["floor"] == "Kat 2"]
    assert tools.AGENDA["source"].startswith("https://kommunity.com/")
