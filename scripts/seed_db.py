"""Demo seed data script for ai-collab-docs.
Usage: python scripts/seed_db.py
Requires: psycopg2 installed, PostgreSQL running at DATABASE_URL
"""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
from passlib.hash import bcrypt

DB_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:5433/forge")

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

now = datetime.now(timezone.utc)

users = [
    ("usr_001", "\u5f20\u4e09", "owner@demo.com", bcrypt.hash("demo123"), "owner"),
    ("usr_002", "\u674e\u56db", "editor@demo.com", bcrypt.hash("demo123"), "editor"),
    ("usr_003", "\u738b\u4e94", "reviewer@demo.com", bcrypt.hash("demo123"), "reviewer"),
    ("usr_004", "\u8d75\u516d", "reader@demo.com", bcrypt.hash("demo123"), "reader"),
]
for uid, name, email, pwd, role in users:
    cur.execute(
        "INSERT INTO users (id, user_id, display_name, email, hashed_password, role, created_at) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
        (uid, name, email, pwd, role, now),
    )

doc_id = "doc_demo_001"
cur.execute(
    "INSERT INTO documents (id, doc_id, title, state, owner_id, anchor_statement, anchor_audience, anchor_argument, "
    "anchor_version, anchor_history, created_at, updated_at) "
    "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (doc_id) DO NOTHING",
    (
        doc_id,
        "Q3\u6280\u672f\u67b6\u6784\u5347\u7ea7\u65b9\u6848",
        "draft",
        "usr_001",
        "\u6784\u5efa\u9762\u5411\u4f01\u4e1a\u6cd5\u52a1\u56e2\u961f\u7684\u5408\u540c\u5ba1\u67e5\u81ea\u52a8\u5316\u5e73\u53f0\uff0c\u8f93\u51fa\u7b26\u5408ISO 27001\u8ba4\u8bc1\u8981\u6c42\u7684\u6280\u672f\u67b6\u6784\u65b9\u6848",
        "\u4f01\u4e1a\u6cd5\u52a1\u56e2\u961f\u3001\u6280\u672f\u7ba1\u7406\u5c42\u3001\u5408\u89c4\u5ba1\u8ba1\u90e8\u95e8",
        "\u901a\u8fc7AI\u9a71\u52a8\u7684\u81ea\u52a8\u5316\u5408\u540c\u5ba1\u67e5\u66ff\u4ee3\u4f20\u7edf\u4eba\u5de5\u5ba1\u67e5\u6d41\u7a0b\uff0c\u4ee5ISO 27001\u4fe1\u606f\u5b89\u5168\u6807\u51c6\u4e3a\u6280\u672f\u57fa\u51c6\uff0c\u6784\u5efa\u5b89\u5168\u3001\u9ad8\u6548\u3001\u5408\u89c4\u7684\u4f01\u4e1a\u7ea7SaaS\u5e73\u53f0",
        1,
        "[]",
        now,
        now,
    ),
)

for uid, role in [("usr_001", "owner"), ("usr_002", "editor"), ("usr_003", "reviewer"), ("usr_004", "reader")]:
    cur.execute(
        "INSERT INTO document_permissions (id, doc_id, user_id, effective_role, joined_at, invited_by) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (doc_id, uid, role, now, "usr_001"),
    )

blocks = [
    ("block_001", 0, "locked-by-human", "usr_001", ""),
    ("block_002", 1, "", "", ""),
    ("block_003", 2, "claimed", "usr_002", ""),
    ("block_004", 3, "", "", ""),
    ("block_005", 4, "drift-warning", "", ""),
]
for bid, order, tags, claimant, locked in blocks:
    tags_json = json.dumps([tags]) if tags else "[]"
    cur.execute(
        "INSERT INTO block_metas (id, block_id, doc_id, tags, claimant_id, drift_score, locked_by, sort_order) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (bid, doc_id, tags_json, claimant, 0.05 * order if tags == "drift-warning" else 0.0, locked, order),
    )

proposals = [
    ("prop_001", "block_001", "doc_ai:TechReviewer", "public",
     "\u5b89\u5168\u4f20\u8f93\u65b9\u6848\u8865\u5145",
     "\u6240\u6709\u6570\u636e\u4f20\u8f93\u91c7\u7528TLS 1.3\u534f\u8bae\u52a0\u5bc6\uff0c\u5e76\u5bf9\u9759\u6001\u6570\u636e\u5b9e\u65bdAES-256\u52a0\u5bc6\u5b58\u50a8\u3002",
     "\u5f53\u524d\u7248\u672c\u7f3a\u5c11\u9759\u6001\u52a0\u5bc6\u63cf\u8ff0\uff0c\u4e0d\u7b26\u5408ISO 27001\u8981\u6c42\u3002",
     0.92, "+45/-12\u884c\uff0c\u8865\u5145\u5b89\u5168\u67b6\u6784\u7ec6\u8282"),
    ("prop_002", "block_002", "doc_ai:TechReviewer", "public",
     "\u6570\u636e\u5e93\u65b9\u6848\u7ec6\u5316",
     "\u91c7\u7528PostgreSQL 15\u4e3b\u4ece\u67b6\u6784\uff0c\u914d\u7f6eWAL\u65e5\u5fd7\u6301\u7eed\u5f52\u6863\u5230S3\u517c\u5bb9\u5b58\u50a8\u3002",
     "\u6570\u636e\u5e93\u65b9\u6848\u63cf\u8ff0\u8fc7\u4e8e\u7b80\u7565\uff0c\u9700\u660e\u786e\u6280\u672f\u9009\u578b\u3002",
     0.88, "+28/-5\u884c\uff0c\u8865\u5145\u6570\u636e\u5e93\u67b6\u6784"),
    ("prop_003", "block_003", "doc_ai:TechReviewer", "public",
     "\u90e8\u7f72\u67b6\u6784\u8865\u5145",
     "\u57fa\u4e8eKubernetes 1.29\u90e8\u7f72\uff0c\u914d\u7f6eHPA\u81ea\u52a8\u6269\u7f29\uff0c\u670d\u52a1\u95f4\u901a\u4fe1\u8d70Service Mesh\u3002",
     "\u90e8\u7f72\u65b9\u6848\u9700\u4f53\u73b0\u4f01\u4e1a\u7ea7\u8fd0\u7ef4\u80fd\u529b\u3002",
     0.85, "+52/-8\u884c\uff0c\u8865\u5145\u90e8\u7f72\u67b6\u6784"),
    ("prop_004", "block_001", "doc_ai:LegalAgent", "public",
     "\u5408\u89c4\u6761\u6b3e\u8865\u5145",
     "\u5185\u7f6e\u5408\u540c\u6761\u6b3e\u5408\u89c4\u68c0\u67e5\u5f15\u64ce\uff0c\u8986\u76d6\u300a\u6c11\u6cd5\u5178\u300b\u5408\u540c\u7f16\u6838\u5fc3\u6761\u6b3e\u3002",
     "\u6cd5\u5f8b\u4f9d\u636e\u9700\u660e\u786e\u5f15\u7528\uff0c\u589e\u5f3a\u6587\u6863\u6743\u5a01\u6027\u3002",
     0.90, "+38/-10\u884c\uff0c\u8865\u5145\u5408\u89c4\u4f9d\u636e"),
    ("prop_005", "block_004", "doc_ai:LegalAgent", "public",
     "\u9690\u79c1\u4fdd\u62a4\u6761\u6b3e",
     "\u7528\u6237\u6570\u636e\u5904\u7406\u4e25\u683c\u9075\u5faa\u300a\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5\u300b\uff0c\u6570\u636e\u6536\u96c6\u9075\u5faa\u6700\u5c0f\u5fc5\u8981\u539f\u5219\u3002",
     "\u9690\u79c1\u4fdd\u62a4\u7f3a\u5c11\u5177\u4f53\u6267\u884c\u6807\u51c6\u3002",
     0.87, "+42/-15\u884c\uff0c\u8865\u5145\u9690\u79c1\u6761\u6b3e"),
    ("prop_006", "block_003", "doc_ai:TechReviewer", "public",
     "\u6269\u5145\u5b89\u5168\u67b6\u6784\u63cf\u8ff0",
     "\u7cfb\u7edf\u5b89\u5168\u67b6\u6784\u91c7\u7528\u7eb5\u6df1\u9632\u5fa1\u6a21\u578b\uff0c\u5305\u542b\u7f51\u7edc\u9694\u79bb\u3001\u5e94\u7528\u5b89\u5168\u3001\u6570\u636e\u5b89\u5168\u4e09\u5c42\u9632\u62a4\u3002",
     "\u5b89\u5168\u67b6\u6784\u63cf\u8ff0\u8fc7\u4e8e\u7b80\u7565\uff0c\u9700\u8865\u5145\u7eb5\u6df1\u9632\u5fa1\u5bbd\u5ea6\u3002",
     0.89, "+48/-10\u884c\uff0c\u6269\u5145\u5b89\u5168\u67b6\u6784"),
    ("prop_007", "block_003", "doc_ai:LegalAgent", "public",
     "\u7cbe\u7b80\u6280\u672f\u7ec6\u8282",
     "\u7cfb\u7edf\u5b89\u5168\u63aa\u65bd\u6ee1\u8db3\u300a\u7f51\u7edc\u5b89\u5168\u6cd5\u300b\u57fa\u672c\u8981\u6c42\uff0c\u5177\u4f53\u6280\u672f\u5b9e\u65bd\u65b9\u6848\u53c2\u89c1\u9644\u5f55\u3002",
     "\u6587\u6863\u9762\u5411\u6cd5\u52a1\u56e2\u961f\uff0c\u8fc7\u591a\u6280\u672f\u7ec6\u8282\u964d\u4f4e\u53ef\u8bfb\u6027\u3002",
     0.86, "-28/+5\u884c\uff0c\u7cbe\u7b80\u6280\u672f\u7ec6\u8282"),
    ("prop_008", "block_002", "personal_ai:\u6211\u7684\u6280\u672f\u987e\u95ee", "private",
     "\u4e8b\u4ef6\u9a71\u52a8\u67b6\u6784\u5f15\u5165",
     "\u5efa\u8bae\u5728\u67b6\u6784\u8bbe\u8ba1\u4e2d\u5f15\u5165\u4e8b\u4ef6\u9a71\u52a8\u6a21\u5f0f\uff0c\u4f7f\u7528\u6d88\u606f\u961f\u5217\u89e3\u8026\u6838\u5fc3\u670d\u52a1\u3002",
     "\u57fa\u4e8e\u4f60\u5bf9\u9ad8\u6269\u5c55\u6027\u7cfb\u7edf\u7684\u504f\u597d\u3002",
     0.84, "+32/-8\u884c\uff0c\u5f15\u5165\u4e8b\u4ef6\u9a71\u52a8"),
    ("prop_009", "block_005", "personal_ai:\u6211\u7684\u6587\u6848\u52a9\u624b", "private",
     "\u4f18\u5316\u8868\u8ff0\u91cf\u5316",
     "\u300c\u7cfb\u7edf\u5177\u5907\u9ad8\u53ef\u7528\u6027\u300d\u6539\u4e3a\u300c\u7cfb\u7edf\u5168\u5e74\u53ef\u7528\u6027\u8fbe99.95%\u300d\u3002",
     "\u91cf\u5316\u8868\u8ff0\u6bd4\u5f62\u5bb9\u8bcd\u66f4\u6709\u8bf4\u670d\u529b\u3002",
     0.91, "+12/-6\u884c\uff0c\u91cf\u5316\u8868\u8ff0"),
]

for i, (pid, bid, source, mem_type, hint, new_txt, rationale, score, summary) in enumerate(proposals):
    old_txt = "\u5f85\u6da6\u8272\u7684\u539f\u59cb\u6bb5\u843d\u5185\u5bb9"
    cur.execute(
        "INSERT INTO ai_proposals (id, proposal_id, block_id, doc_id, ai_source, ai_memory_type, old_content, "
        "new_content, rationale, anchor_alignment_score, diff_summary, created_at, status) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (pid, bid, doc_id, source, mem_type, old_txt, new_txt, rationale, score, summary,
         now - timedelta(hours=i), "pending"),
    )

memories = [
    (doc_id, "usr_001", "TechReviewer",
     "\u5b89\u5168\u67b6\u6784\u63cf\u8ff0\u5fc5\u987b\u6709\u7eb5\u6df1\u9632\u5fa1\u5bbd\u5ea6\u7684\u8986\u76d6",
     "public", True, 4),
    (doc_id, "", "LegalAgent",
     "\u6cd5\u5f8b\u5408\u89c4\u6761\u6b3e\u4f18\u5148\uff0c\u6280\u672f\u7ec6\u8282\u653e\u5165\u9644\u5f55",
     "public", True, 3),
    (doc_id, "usr_001", "TechReviewer",
     "\u6570\u636e\u5e93\u9009\u578b\u9700\u660e\u786e\u6280\u672f\u6808\u5e76\u8bf4\u660e\u9ad8\u53ef\u7528\u7b56\u7565",
     "public", False, 2),
    (doc_id, "usr_001", "\u6211\u7684\u6280\u672f\u987e\u95ee",
     "\u4f18\u5148\u4f7f\u7528\u5f02\u6b65\u4e8b\u4ef6\u9a71\u52a8\u67b6\u6784\u63d0\u9ad8\u53ef\u6269\u5c55\u6027",
     "private", True, 3),
    (doc_id, "usr_002", "\u6211\u7684\u6587\u6848\u52a9\u624b",
     "\u4f7f\u7528\u91cf\u5316\u6570\u636e\u66ff\u4ee3\u5f62\u5bb9\u8bcd\u589e\u5f3a\u6587\u6863\u4e13\u4e1a\u6027",
     "private", False, 2),
]

for did, uid, role, rule, mtype, solidified, count in memories:
    cur.execute(
        "INSERT INTO ai_memories (id, doc_id, user_id, ai_role, rule, memory_type, solidified, trigger_count, created_at) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (did, uid, role, rule, mtype, solidified, count, now),
    )

arb_id = "arb_001"
cur.execute(
    "INSERT INTO arbitrations (id, arb_id, doc_id, block_id, conflict_type, proposals_json, ai_sources_json, "
    "claimant_id, created_at) "
    "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
    (arb_id, doc_id, "block_003", "mixed", json.dumps(["prop_006", "prop_007"]),
     json.dumps(["doc_ai:TechReviewer", "doc_ai:LegalAgent"]), "usr_002", now),
)

actions = [
    "create_document", "update_title", "request_forge", "approve_proposal",
    "state_transition", "block_claim", "conflict_detected", "start_review",
]
for i, action in enumerate(actions):
    op_id = "op_%03d" % i
    target = doc_id if i < 5 else "prop_00%d" % i
    cur.execute(
        "INSERT INTO operation_logs (id, op_id, user_id, action, target_type, target_id, doc_id, "
        "before_state, after_state, timestamp) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            op_id,
            "usr_001" if i % 2 == 0 else "usr_003",
            action,
            "document" if i < 5 else "proposal",
            target,
            doc_id,
            "draft",
            action.replace("_", " "),
            now - timedelta(hours=len(actions) - i),
        ),
    )

conn.commit()
cur.close()
conn.close()

print("Demo seed data inserted successfully!")
print("Demo accounts:")
print("  owner@demo.com / demo123 (\u5f20\u4e09, Owner)")
print("  editor@demo.com / demo123 (\u674e\u56db, Editor)")
print("  reviewer@demo.com / demo123 (\u738b\u4e94, Reviewer)")
print("  reader@demo.com / demo123 (\u8d75\u516d, Reader)")
