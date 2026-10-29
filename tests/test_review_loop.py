
from app.graphs.supervisor_graph import (
    after_review,
    parse_review,
    revise,
)


def test_approved_review_completes():
    assert after_review({
        "review_status": "approved",
        "revision_count": 0,
        "max_revisions": 2,
    }) == "complete"


def test_changes_requested_returns_to_developer():
    assert after_review({
        "review_status": "changes_requested",
        "revision_count": 0,
        "max_revisions": 2,
    }) == "revise"


def test_revision_limit_blocks_workflow():
    assert after_review({
        "review_status": "changes_requested",
        "revision_count": 2,
        "max_revisions": 2,
    }) == "blocked"


def test_invalid_review_blocks_workflow():
    status, feedback = parse_review("Looks good!")

    assert status == "blocked"
    assert feedback


def test_valid_review_json():
    status, feedback = parse_review(
        '{"status":"changes_requested",'
        '"feedback":"Add a missing test."}'
    )

    assert status == "changes_requested"
    assert feedback == "Add a missing test."


def test_revision_resets_developer_and_tester():
    result = revise({
        "selected_agents": [
            "architect",
            "developer",
            "tester",
            "reviewer",
        ],
        "revision_count": 0,
        "outputs": {
            "architect": "Architecture",
            "developer": "Initial code",
            "tester": "QA findings",
            "reviewer": "Changes requested",
        },
    })

    assert result["revision_count"] == 1
    assert result["current_index"] == 1
    assert result["outputs"] == {
        "architect": "Architecture",
    }
