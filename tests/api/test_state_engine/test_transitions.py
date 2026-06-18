from contracts.contracts import DocumentState, UserRole
from state_engine.engine import state_engine


def test_transition_draft_to_discussion():
    assert state_engine.guard_transition(DocumentState.DRAFT, DocumentState.DISCUSSION, UserRole.EDITOR) is True
    assert state_engine.guard_transition(DocumentState.DRAFT, DocumentState.DISCUSSION, UserRole.READER) is False


def test_transition_discussion_to_review():
    assert state_engine.guard_transition(DocumentState.DISCUSSION, DocumentState.REVIEW, UserRole.LEAD_EDITOR) is True
    assert state_engine.guard_transition(DocumentState.DISCUSSION, DocumentState.REVIEW, UserRole.EDITOR) is False


def test_transition_review_to_finalized():
    assert state_engine.guard_transition(DocumentState.REVIEW, DocumentState.FINALIZED, UserRole.OWNER) is True
    assert state_engine.guard_transition(DocumentState.REVIEW, DocumentState.FINALIZED, UserRole.REVIEWER) is False


def test_no_backward_transition():
    assert state_engine.guard_transition(DocumentState.REVIEW, DocumentState.DISCUSSION, UserRole.OWNER) is False
    assert state_engine.guard_transition(DocumentState.FINALIZED, DocumentState.DRAFT, UserRole.OWNER) is False


def test_allowed_transitions_draft():
    transitions = state_engine.get_allowed_transitions(DocumentState.DRAFT, UserRole.OWNER)
    assert DocumentState.DISCUSSION in transitions
    assert DocumentState.ARCHIVED in transitions


def test_allowed_transitions_review():
    transitions = state_engine.get_allowed_transitions(DocumentState.REVIEW, UserRole.OWNER)
    assert DocumentState.FINALIZED in transitions
