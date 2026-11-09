"""Issue classifier: bug fixes from v9 + safety cases that must keep working."""
import pytest

FIXED_BUGS = [
    ("There is a flood threat in Ratnapura", "disaster_alert"),
    ("neighbour is burning plastic every night", "environment_issue"),
    ("ගෙදර ළඟ කුණු පුළුස්සනවා", "environment_issue"),
    ("is it advisable to complain about water supply", "water_issue"),
]
NOT_THIS = [
    ("Someone is threatening to cut down trees near the river", "women_child_safety"),
    ("වැස්ස ගහනවා පාරේ වතුර", "women_child_safety"),
    ("kade eka business eka wahala", "bus_complaint"),
]
SAFETY = [
    "someone is threatening me every day",
    "my husband threatened to kill me",
    "mata kenek follow karanawa",
    "ළමයාට ගහනවා",
    "lamayata gahanawa",
    "child abuse in our area",
    "sexual harassment at bus stop",
]
OTHER = [
    ("bus eke conductor balance dunne na", "bus_complaint"),
    ("para kadila loku walak", "road_issue"),
    ("apita wathura na dawas 3k", "water_issue"),
    ("current eka na", "electricity_issue"),
    ("I lost my passport", "lost_document"),
    ("garbage collect karanne na sathi dekak", "garbage_collection"),
    ("landslide warning in Badulla", "disaster_alert"),
]


@pytest.mark.parametrize("text,expected", FIXED_BUGS + OTHER)
def test_label(classifier, text, expected):
    assert classifier.predict(text)["label"] == expected


@pytest.mark.parametrize("text,wrong", NOT_THIS)
def test_not_misclassified(classifier, text, wrong):
    assert classifier.predict(text)["label"] != wrong


@pytest.mark.parametrize("text", SAFETY)
def test_safety_always_caught(classifier, text):
    assert classifier.predict(text)["label"] == "women_child_safety"
