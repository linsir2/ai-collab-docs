from contracts.contracts import TRANSITION_RULES, DocumentState, UserRole


class StateEngine:
    def __init__(self):
        self.rules: dict[tuple[DocumentState, DocumentState], set[UserRole]] = {}
        for from_state, to_state, allowed_roles in TRANSITION_RULES:
            key = (from_state, to_state)
            self.rules[key] = set(allowed_roles)

    def guard_transition(self, from_state: DocumentState, to_state: DocumentState, user_role: UserRole) -> bool:
        key = (from_state, to_state)
        allowed = self.rules.get(key, set())
        return user_role in allowed

    def get_allowed_transitions(self, current_state: DocumentState, user_role: UserRole) -> list[DocumentState]:
        result = []
        for (from_state, to_state), allowed_roles in self.rules.items():
            if from_state == current_state and user_role in allowed_roles:
                result.append(to_state)
        return result

    def get_all_states(self) -> list[DocumentState]:
        return list(DocumentState)

    def is_valid_state(self, state: str) -> bool:
        try:
            DocumentState(state)
            return True
        except ValueError:
            return False

    def requires_all_approvals(self, from_state: DocumentState, to_state: DocumentState) -> bool:
        return from_state == DocumentState.REVIEW and to_state == DocumentState.FINALIZED


state_engine = StateEngine()
