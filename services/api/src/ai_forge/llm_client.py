import random

from ai_forge.mock_data import CONFLICT_PAIRS, LEGAL_AGENT_FORGES, PERSONAL_AI_FORGES, TECH_REVIEWER_FORGES

DOC_AI_FORGES_MAP = {
    "TechReviewer": TECH_REVIEWER_FORGES,
    "LegalAgent": LEGAL_AGENT_FORGES,
}


class MockLLMClient:
    def forge(
        self,
        anchor_statement: str,
        block_content: str,
        block_context: str,
        ai_role: str,
        ai_source: str,
        instruction: str,
    ) -> dict:
        proposals_list: list[dict] = []
        if ai_source.startswith("personal_ai"):
            for entry in PERSONAL_AI_FORGES:
                if entry["role"] == ai_role:
                    proposals_list = entry["proposals"]
                    break
        else:
            for entry_name, entries in DOC_AI_FORGES_MAP.items():
                for entry in entries:
                    if entry["role"] == ai_role:
                        proposals_list = entry["proposals"]
                        break

        matched = None
        for p in proposals_list:
            hints = p.get("instruction_hint", "").split("|")
            if any(h.lower() in instruction.lower() for h in hints if h):
                matched = p
                break

        if not matched and proposals_list:
            matched = proposals_list[0]

        if not matched:
            doc_forge = DOC_AI_FORGES_MAP.get("TechReviewer", [])
            if doc_forge:
                matched = doc_forge[0]["proposals"][0]

        score = round(0.7 + random.random() * 0.25, 4)
        return {
            "new_content": matched["new_text"],
            "rationale": matched["rationale"],
            "diff_summary": matched["diff_summary"],
            "anchor_alignment_score": score,
        }

    def review(self, anchor_statement: str, snapshot_content: str, dimension: str, ai_role: str) -> dict:
        return {
            "verdict": "pass",
            "issues": [],
            "suggestions": [],
        }

    def detect_conflict(
        self,
        proposal_a_content: str,
        proposal_b_content: str,
        proposal_a_rationale: str,
        proposal_b_rationale: str,
    ) -> dict:
        for pair in CONFLICT_PAIRS:
            a = pair["proposal_a"]
            b = pair["proposal_b"]
            a_match = a["new_content"] in proposal_a_content or a["rationale"] in proposal_a_rationale
            b_match = b["new_content"] in proposal_b_content or b["rationale"] in proposal_b_rationale
            if a_match and b_match:
                return {
                    "is_opposing": True,
                    "conflict_description": pair["conflict_reason"],
                }

        expand_keywords = ["扩充", "补充", "详细", "增加", "深入", "完整"]
        reduce_keywords = ["精简", "删除", "缩减", "移至附录", "简略", "去除"]
        a_expands = any(k in proposal_a_rationale for k in expand_keywords)
        a_reduces = any(k in proposal_a_rationale for k in reduce_keywords)
        b_expands = any(k in proposal_b_rationale for k in expand_keywords)
        b_reduces = any(k in proposal_b_rationale for k in reduce_keywords)

        if (a_expands and b_reduces) or (a_reduces and b_expands):
            return {
                "is_opposing": True,
                "conflict_description": "两提案对内容详略方向存在对立：一方建议扩充，另一方建议精简。",
            }

        return {
            "is_opposing": False,
            "conflict_description": "",
        }
