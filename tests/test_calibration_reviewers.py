"""Two-reviewer attribution, inter-rater agreement and uncertainty (T-053).

Synthetic labels only. No provider is called and no real reviewer's work is used. These
tests assert the mechanics; the actual human labels remain external work, and nothing here
should be read as evidence that any Judge is calibrated.
"""

import json
import math

import pytest
from test_judge_calibration import make_run, selection

from app import database as db
from app.blackbox import governance, metering
from app.blackbox import judge_calibration as cal
from app.blackbox.calibration_models import (
    KIND_EVALUATION,
    KIND_SET,
    OWNER,
    CalibrationPolicy,
    LabelUpdate,
    Sample,
)


@pytest.fixture
def stored_set():
    """A real saved calibration set, so storage guards are exercised, not just computed."""
    run = make_run(scenarios=3)
    created = cal.create_set("reviewers", selection(run, sample=Sample(size=3, seed=1)))
    record = cal.get_set(created["set"]["id"])
    return record, record["draft"]["items"][0]


@pytest.fixture(autouse=True)
def only_this_file_records():
    """Remove the records this file creates so later tests never see them."""
    yield
    with db.connect() as conn:
        governance.initialize(conn)
        metering.init_db(conn)
        for kind in (KIND_SET, KIND_EVALUATION, "blackbox", "assurance"):
            conn.execute("DELETE FROM records WHERE kind=?", (kind,))
        conn.execute("DELETE FROM audit_chain")


def item(ident: str, category: str = "functional", base: str | None = None) -> dict:
    return {
        "id": ident,
        "category": category,
        "source": {"base_case_id": base or ident},
        "payload_hash": "p" + ident,
        "source_hash": "s" + ident,
        "transcript_hash": "t" + ident,
        "labels": [],
        "second_labels": [],
    }


def label(author: str, passed: bool, revision: int = 1) -> dict:
    return {
        "revision": revision,
        "verdict": "pass" if passed else "fail",
        "binary_pass": passed,
        "score": 90.0 if passed else 10.0,
        "rationale": "synthetic",
        "author": author,
        "at": "2026-11-09T00:00:00Z",
        "change_reason": "",
    }


def labelled(specs, primary="Reviewer A", second="Reviewer B") -> list[dict]:
    """Build items from (id, primary_pass, second_pass) triples; second may be None."""
    items = []
    for index, (ident, first, other) in enumerate(specs):
        row = item(ident, base=f"scenario-{index}")
        row["labels"] = [label(primary, first)]
        if other is not None:
            row["second_labels"] = [label(second, other)]
        items.append(row)
    return items


# --- the interval ---------------------------------------------------------------------------


def test_the_interval_is_wilson_and_stays_inside_zero_to_one_hundred():
    tight = cal.wilson_interval(50, 50)
    assert tight["point_percent"] == 100.0
    assert tight["high_percent"] <= 100.0
    assert tight["low_percent"] > 0
    # A normal approximation would run past 100% here; Wilson must not.
    assert cal.wilson_interval(10, 10)["high_percent"] <= 100.0
    assert cal.wilson_interval(0, 10)["low_percent"] >= 0.0


def test_a_smaller_sample_gives_a_wider_interval():
    small = cal.wilson_interval(9, 10)
    large = cal.wilson_interval(90, 100)
    assert small["point_percent"] == large["point_percent"] == 90.0
    small_width = small["high_percent"] - small["low_percent"]
    large_width = large["high_percent"] - large["low_percent"]
    assert small_width > large_width, "ten observations cannot be as precise as a hundred"


def test_no_observations_have_no_interval():
    assert cal.wilson_interval(0, 0) is None
    assert cal.wilson_interval(1, 0) is None
    assert cal.wilson_interval(5, 4) is None


# --- correlated repeats ---------------------------------------------------------------------


def test_repeats_of_one_scenario_count_as_one_observation():
    """Three repeats of the same question are not three independent observations."""
    rows = [item(f"i{n}", base="same-scenario") for n in range(3)]
    pairs = [(row, {"agrees": True}) for row in rows]
    agreeing, total = cal.scenario_outcomes(pairs)
    assert (agreeing, total) == (1, 1)


def test_distinct_scenarios_each_count_once():
    rows = [item(f"i{n}", base=f"scenario-{n}") for n in range(4)]
    pairs = [(row, {"agrees": True}) for row in rows]
    assert cal.scenario_outcomes(pairs) == (4, 4)


def test_a_scenario_needs_a_majority_of_its_repeats_to_agree():
    rows = [item(f"i{n}", base="one") for n in range(4)]
    # An even split counts against agreement, which is the conservative reading.
    half = [
        (rows[0], {"agrees": True}),
        (rows[1], {"agrees": True}),
        (rows[2], {"agrees": False}),
        (rows[3], {"agrees": False}),
    ]
    assert cal.scenario_outcomes(half) == (0, 1)
    majority = half[:3] + [(rows[3], {"agrees": True})]
    assert cal.scenario_outcomes(majority) == (1, 1)


def test_the_interval_unit_is_the_scenario_not_the_item():
    """Twelve repeats of three scenarios must not be reported as twelve observations."""
    rows = []
    for scenario in range(3):
        rows += [item(f"i{scenario}-{n}", base=f"scenario-{scenario}") for n in range(4)]
    entry = cal.metrics(
        rows,
        {
            row["id"]: {
                "status": "judged",
                "actual": {"id": "E"},
                "agrees": True,
                "judge_pass": True,
            }
            for row in rows
        },
        "E",
        CalibrationPolicy(),
    )
    # No labels, so nothing is comparable and there is no interval to report.
    assert entry["agreement_interval"] is None
    for row in rows:
        row["labels"] = [label(OWNER, True)]
    entry = cal.metrics(
        rows,
        {
            row["id"]: {
                "status": "judged",
                "actual": {"id": "E"},
                "agrees": True,
                "judge_pass": True,
            }
            for row in rows
        },
        "E",
        CalibrationPolicy(),
    )
    assert entry["agreement_interval"]["total"] == 3
    assert entry["agreement_interval"]["unit"] == "distinct scenario"


# --- inter-rater agreement -------------------------------------------------------------------


def test_one_reviewer_reports_single_reviewer_and_no_kappa():
    items = labelled([("a", True, None), ("b", False, None)])
    found = cal.reviewer_agreement(items, CalibrationPolicy())
    assert found["status"] == "single_reviewer"
    assert found["reviewer_count"] == 1
    assert found["independent"] is False
    assert found["cohens_kappa"] is None
    assert found["paired_items"] == 0


def test_the_same_person_twice_is_not_two_reviewers():
    """The brief's trap: two copies of one person's labels are not independent evidence."""
    items = labelled([("a", True, True)], primary="Hussain", second="hussain")
    found = cal.reviewer_agreement(items, CalibrationPolicy())
    assert found["status"] == "not_independent"
    assert found["independent"] is False
    assert found["reviewer_count"] == 1


def test_two_reviewers_give_agreement_and_a_chance_corrected_kappa():
    specs = [(f"i{n}", n % 2 == 0, n % 2 == 0) for n in range(8)]
    specs[0] = ("i0", True, False)
    items = labelled(specs)
    found = cal.reviewer_agreement(items, CalibrationPolicy())
    assert found["status"] == "measured"
    assert found["independent"] is True
    assert found["reviewer_count"] == 2
    assert found["paired_items"] == 8
    assert found["agreement"] == {"numerator": 7, "denominator": 8, "percent": 87.5}
    assert found["disagreement_ids"] == ["i0"]
    assert found["cohens_kappa"] is not None
    # Kappa is below raw agreement because some agreement is expected by chance.
    assert found["cohens_kappa"] < 0.875
    assert found["table"]["primary_pass_second_fail"] == 1


def test_kappa_is_undefined_when_both_reviewers_used_one_class():
    """Total chance agreement makes kappa meaningless; raw agreement must not stand in."""
    items = labelled([(f"i{n}", True, True) for n in range(5)])
    found = cal.reviewer_agreement(items, CalibrationPolicy())
    assert found["agreement"]["percent"] == 100.0
    assert found["cohens_kappa"] is None
    assert "Undefined" in found["kappa_note"]


def test_reviewers_below_the_threshold_are_reported_as_such():
    specs = [(f"i{n}", True, n < 2) for n in range(5)]
    items = labelled(specs)
    found = cal.reviewer_agreement(items, CalibrationPolicy(min_reviewer_agreement_percent=80))
    assert found["status"] == "below_threshold"
    assert found["agreement"]["percent"] == 40.0


def test_two_reviewers_without_overlapping_items_have_no_agreement():
    items = labelled([("a", True, None), ("b", False, None)])
    items[1]["labels"] = []
    items[1]["second_labels"] = [label("Reviewer B", False)]
    found = cal.reviewer_agreement(items, CalibrationPolicy())
    assert found["status"] == "no_overlap"
    assert found["paired_items"] == 0


def test_human_agreement_is_kept_separate_from_judge_agreement():
    """Reviewer agreement must never be presented as the Judge's agreement."""
    items = labelled([(f"i{n}", True, True) for n in range(3)])
    results = {
        row["id"]: {
            "status": "judged",
            "actual": {"id": "E"},
            "agrees": False,
            "judge_pass": False,
        }
        for row in items
    }
    entry = cal.metrics(items, results, "E", CalibrationPolicy())
    assert entry["reviewers"]["agreement"]["percent"] == 100.0
    assert entry["agreement"]["percent"] == 0.0
    assert "does not measure the Judge" in entry["reviewers"]["limitation"]


# --- states and warnings ---------------------------------------------------------------------


def test_a_single_reviewer_sample_keeps_its_caveat_even_when_it_meets_the_threshold():
    p = CalibrationPolicy(
        min_distinct_scenarios=2, min_human_pass_scenarios=1, min_human_fail_scenarios=1
    )
    items = labelled([("a", True, None), ("b", False, None)])
    results = {
        "a": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": True},
        "b": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": False},
    }
    entry = cal.metrics(items, results, "E", p)
    state, warnings = cal.classify(entry, p, True)
    assert state == "meets"
    assert cal.WARNINGS["single_reviewer"] in warnings


def test_a_policy_requiring_two_reviewers_makes_one_reviewer_insufficient():
    p = CalibrationPolicy(
        min_reviewers=2,
        min_distinct_scenarios=2,
        min_human_pass_scenarios=1,
        min_human_fail_scenarios=1,
    )
    items = labelled([("a", True, None), ("b", False, None)])
    results = {
        "a": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": True},
        "b": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": False},
    }
    entry = cal.metrics(items, results, "E", p)
    check = next(c for c in entry["sufficiency"]["checks"] if c["name"] == "independent_reviewers")
    assert check["required"] == 2 and check["actual"] == 1 and check["met"] is False
    assert cal.classify(entry, p, True)[0] == "insufficient_sample"


def test_a_wide_interval_is_flagged():
    p = CalibrationPolicy(
        min_distinct_scenarios=2, min_human_pass_scenarios=1, min_human_fail_scenarios=1
    )
    items = labelled([("a", True, None), ("b", False, None)])
    results = {
        "a": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": True},
        "b": {"status": "judged", "actual": {"id": "E"}, "agrees": True, "judge_pass": False},
    }
    entry = cal.metrics(items, results, "E", p)
    # Two scenarios cannot support a precise estimate.
    assert (
        entry["agreement_interval"]["high_percent"] - entry["agreement_interval"]["low_percent"]
        > 20
    )
    assert cal.WARNINGS["wide_interval"] in cal.classify(entry, p, True)[1]


# --- storage, attribution and blinding --------------------------------------------------------


def test_the_second_reviewer_cannot_be_the_first_reviewer(stored_set):
    """The brief's trap, enforced at the storage boundary rather than only computed."""
    record, first = stored_set
    cal.save_label(
        record["id"],
        first["id"],
        LabelUpdate(expected_revision=0, verdict="pass", reviewer="Hussain"),
    )
    with pytest.raises(cal.CalibrationError, match="different person"):
        cal.save_label(
            record["id"],
            first["id"],
            # Same person, different capitalisation: still one reviewer.
            LabelUpdate(expected_revision=0, verdict="fail", reviewer="hussain", role="second"),
        )
    saved = cal.save_label(
        record["id"],
        first["id"],
        LabelUpdate(expected_revision=0, verdict="fail", reviewer="Mouni", role="second"),
    )
    assert saved["role"] == "second" and saved["reviewer"] == "Mouni"
    stored = cal.get_set(record["id"])["draft"]["items"]
    row = next(i for i in stored if i["id"] == first["id"])
    assert row["labels"][-1]["author"] == "Hussain"
    assert row["second_labels"][-1]["author"] == "Mouni"
    assert cal.reviewer_names(stored) == {"primary": "Hussain", "second": "Mouni"}


def test_a_second_review_needs_a_primary_judgement_first(stored_set):
    record, first = stored_set
    with pytest.raises(cal.CalibrationError, match="primary reviewer first"):
        cal.save_label(
            record["id"],
            first["id"],
            LabelUpdate(expected_revision=0, verdict="pass", reviewer="Mouni", role="second"),
        )


def test_one_stream_belongs_to_one_person(stored_set):
    record, first = stored_set
    cal.save_label(
        record["id"],
        first["id"],
        LabelUpdate(expected_revision=0, verdict="pass", reviewer="Hussain"),
    )
    second = cal.get_set(record["id"])["draft"]["items"][1]
    with pytest.raises(cal.CalibrationError, match="belong to Hussain"):
        cal.save_label(
            record["id"],
            second["id"],
            LabelUpdate(expected_revision=0, verdict="pass", reviewer="Someone Else"),
        )


def test_the_audit_chain_records_who_labelled_and_in_which_role(stored_set):
    record, first = stored_set
    cal.save_label(
        record["id"],
        first["id"],
        LabelUpdate(expected_revision=0, verdict="pass", reviewer="Hussain"),
    )
    cal.save_label(
        record["id"],
        first["id"],
        LabelUpdate(expected_revision=0, verdict="fail", reviewer="Mouni", role="second"),
    )
    with db.connect() as conn:
        rows = [
            json.loads(r[0])
            for r in conn.execute(
                "SELECT body FROM audit_chain WHERE run_id=?", (record["id"],)
            ).fetchall()
        ]
    saved = [r for r in rows if r.get("event") == "label_saved"]
    assert len(saved) == 2
    assert {r["reviewer"] for r in saved} == {"Hussain", "Mouni"}
    assert {r["role"] for r in saved} == {"primary", "second"}


def test_a_blind_second_review_does_not_see_the_first_label():
    row = item("a")
    row["labels"] = [label("Reviewer A", True)]
    row["second_labels"] = [label("Reviewer B", False)]
    second = cal.public_item(row, role="second")
    assert second["label"]["author"] == "Reviewer B"
    assert second["label"]["binary_pass"] is False
    assert second["primary_label_exists"] is True
    # Neither raw stream is exposed, so the first reviewer's verdict cannot leak.
    assert "labels" not in second and "second_labels" not in second
    primary = cal.public_item(row, role="primary")
    assert primary["label"]["author"] == "Reviewer A"
    assert primary["second_label_exists"] is True
    assert "labels" not in primary and "second_labels" not in primary


def test_freezing_covers_the_second_reviewer_so_a_later_change_is_detectable():
    row = item("a")
    row["labels"] = [label("Reviewer A", True)]
    before = cal.version_hash([row])
    row["second_labels"] = [label("Reviewer B", False)]
    after = cal.version_hash([row])
    assert before != after, "a second reviewer's label must change the frozen version"
    # The reviewer's identity is part of the frozen identity too.
    renamed = item("a")
    renamed["labels"] = [label("Someone Else", True)]
    assert cal.version_hash([renamed]) != before


def test_reviewer_names_treats_an_unattributed_legacy_label_as_the_owner():
    row = item("a")
    row["labels"] = [{k: v for k, v in label("x", True).items() if k != "author"}]
    assert cal.reviewer_names([row]) == {"primary": OWNER}


@pytest.mark.parametrize("role", ["primary", "second"])
def test_label_updates_carry_a_reviewer_and_a_role(role):
    update = LabelUpdate(expected_revision=0, verdict="pass", reviewer="Reviewer A", role=role)
    assert update.reviewer == "Reviewer A" and update.role == role
    assert update.binary is True


def test_a_label_update_defaults_to_the_primary_owner():
    update = LabelUpdate(expected_revision=0, verdict="fail")
    assert update.reviewer == OWNER and update.role == "primary"


def test_an_empty_reviewer_name_is_rejected():
    with pytest.raises(ValueError):
        LabelUpdate(expected_revision=0, verdict="pass", reviewer="")


def test_kappa_matches_the_textbook_formula():
    """A worked example, so the implementation is not merely self-consistent."""
    # 10 paired items: both pass 5, both fail 2, primary pass only 2, primary fail only 1.
    specs = (
        [(f"p{n}", True, True) for n in range(5)]
        + [(f"f{n}", False, False) for n in range(2)]
        + [(f"x{n}", True, False) for n in range(2)]
        + [("y0", False, True)]
    )
    found = cal.reviewer_agreement(labelled(specs), CalibrationPolicy())
    observed = 7 / 10
    primary_pass, second_pass = 7 / 10, 6 / 10
    expected = primary_pass * second_pass + (1 - primary_pass) * (1 - second_pass)
    assert math.isclose(found["cohens_kappa"], (observed - expected) / (1 - expected), abs_tol=1e-4)
