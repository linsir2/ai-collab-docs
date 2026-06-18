#!/usr/bin/env python3
"""WebSocket 多用户协作测试脚本

针对运行中的后端 (http://127.0.0.1:8000) 执行以下测试:
  A. 登录 4 个用户 (owner/editor/reviewer/reader)
  B. 查找种子文档 doc_id
  C. 连接 4 个 WebSocket 客户端
  D. 验证所有连接
  E. 编辑者发送 PROPOSAL_CREATED — 检查是否广播
  F. 读者发送 STATE_CHANGE — 应被拒绝
  G. 所有者发送 STATE_CHANGE — 应被接受
  H. 速率限制测试 — 70 条消息
  I. 汇总报告
"""
import asyncio
import json
import sys
import urllib.error
import urllib.request

import websockets

BASE_HTTP = "http://127.0.0.1:8000"
BASE_WS = "ws://127.0.0.1:8000"
HTTP_TIMEOUT = 10
WS_RECV_TIMEOUT = 3.0

USERS = {
    "owner":    {"email": "owner@demo.com",    "password": "demo123"},
    "editor":   {"email": "editor@demo.com",   "password": "demo123"},
    "reviewer": {"email": "reviewer@demo.com", "password": "demo123"},
    "reader":   {"email": "reader@demo.com",   "password": "demo123"},
}


# ============================================================
# HTTP 辅助函数 (urllib.request)
# ============================================================

def http_post_json(url: str, payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read())


def http_get_json(url: str, token: str) -> dict | list:
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}"}, method="GET"
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read())


def login(email: str, password: str) -> dict:
    return http_post_json(
        f"{BASE_HTTP}/api/auth/login", {"email": email, "password": password}
    )


def find_doc_id(token: str) -> str | None:
    docs = http_get_json(f"{BASE_HTTP}/api/documents", token)
    if isinstance(docs, list) and docs:
        return docs[0]["doc_id"]
    return None


# ============================================================
# WebSocket 辅助函数
# ============================================================

async def drain(ws, timeout: float = 0.5) -> list:
    """排空 WebSocket 待处理消息，返回消息列表。"""
    messages = []
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            try:
                messages.append(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                messages.append(raw)
        except (TimeoutError, asyncio.TimeoutError):
            break
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception:
            break
    return messages


async def drain_all(clients: dict, timeout: float = 0.5):
    """排空所有客户端的待处理消息。"""
    for ws in clients.values():
        await drain(ws, timeout=timeout)


async def recv_json(ws, timeout: float = WS_RECV_TIMEOUT) -> dict | None:
    """接收一条 JSON 消息，超时返回 None。"""
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw)
    except (TimeoutError, asyncio.TimeoutError):
        return None
    except websockets.exceptions.ConnectionClosed as e:
        return {"_closed": True, "code": e.code, "reason": e.reason}
    except Exception as e:
        return {"_error": str(e)}


async def send_json(ws, obj: dict):
    await ws.send(json.dumps(obj))


def is_open(ws) -> bool:
    try:
        return ws.state.name == "OPEN"
    except AttributeError:
        try:
            return ws.open
        except Exception:
            return False


async def reconnect(label: str, doc_id: str, tokens: dict, clients: dict):
    """重连一个客户端并排空其他客户端的 user_joined 消息。"""
    old = clients.get(label)
    if old:
        try:
            await old.close()
        except Exception:
            pass
    uri = f"{BASE_WS}/api/collab/ws/{doc_id}?token={tokens[label]}"
    ws = await websockets.connect(uri)
    clients[label] = ws
    await asyncio.sleep(0.3)
    for name, w in clients.items():
        if name != label:
            await drain(w, timeout=0.2)
    return ws


# ============================================================
# 主测试流程
# ============================================================

async def main():
    results = {}
    clients: dict = {}

    # ================================================================
    # A. 登录所有用户
    # ================================================================
    print("=" * 70)
    print("A. 登录所有用户 (POST /api/auth/login)")
    print("=" * 70)
    tokens: dict[str, str] = {}
    user_infos: dict[str, dict] = {}
    for label, creds in USERS.items():
        try:
            resp = login(creds["email"], creds["password"])
            tokens[label] = resp["access_token"]
            user_infos[label] = resp["user"]
            print(
                f"  [OK]   {label:8s} user_id={resp['user']['user_id']}  "
                f"global_role={resp['user']['global_role']}"
            )
        except Exception as e:
            print(f"  [FAIL] {label:8s} 登录失败: {e}")
    results["A_login"] = {name: (name in tokens) for name in USERS}
    if len(tokens) < 4:
        print("\n[ABORT] 登录失败，无法继续测试。")
        return results

    # ================================================================
    # B. 查找种子文档 doc_id
    # ================================================================
    print()
    print("=" * 70)
    print("B. 查找种子文档 (GET /api/documents)")
    print("=" * 70)
    try:
        doc_id = find_doc_id(tokens["owner"])
    except Exception as e:
        print(f"  [FAIL] 查询文档失败: {e}")
        return results
    results["B_doc_id"] = doc_id
    if doc_id:
        print(f"  [OK]   找到文档: doc_id = {doc_id}")
    else:
        print("  [FAIL] 未找到任何文档")
        return results

    # ================================================================
    # C. 连接 4 个 WebSocket 客户端
    # ================================================================
    print()
    print("=" * 70)
    print("C. 连接 4 个 WebSocket 客户端")
    print(f"    {BASE_WS}/api/collab/ws/{doc_id}?token=...")
    print("=" * 70)
    for label in ["owner", "editor", "reviewer", "reader"]:
        uri = f"{BASE_WS}/api/collab/ws/{doc_id}?token={tokens[label]}"
        try:
            ws = await websockets.connect(uri)
            clients[label] = ws
            print(f"  [OK]   {label:8s} WebSocket 连接成功")
        except Exception as e:
            print(f"  [FAIL] {label:8s} WebSocket 连接失败: {e}")
    results["C_connect"] = {name: (name in clients) for name in USERS}

    # ================================================================
    # D. 验证所有连接
    # ================================================================
    print()
    print("=" * 70)
    print("D. 验证所有连接")
    print("=" * 70)
    connected = sum(1 for ws in clients.values() if is_open(ws))
    results["D_verify"] = {"connected": connected, "expected": 4}
    if connected == 4:
        print("  [OK]   全部 4 个连接已建立")
    else:
        print(f"  [WARN] 仅 {connected}/4 个连接成功")

    # 排空 user_joined 消息
    await asyncio.sleep(0.5)
    await drain_all(clients)

    # ================================================================
    # E. 编辑者发送 PROPOSAL_CREATED — 检查是否广播
    # ================================================================
    print()
    print("=" * 70)
    print('E. 编辑者发送 PROPOSAL_CREATED — 检查是否广播')
    print("=" * 70)
    await drain_all(clients)

    proposal_msg = {
        "type": "PROPOSAL_CREATED",
        "block_id": "blk-001",
        "content": "test proposal",
    }
    try:
        await send_json(clients["editor"], proposal_msg)
        print("  [INFO] editor 已发送 PROPOSAL_CREATED")
    except Exception as e:
        print(f"  [FAIL] editor 发送失败: {e}")

    e_results = {}
    e_broadcast_count = 0
    for label in ["owner", "editor", "reviewer", "reader"]:
        ws = clients.get(label)
        if ws is None or not is_open(ws):
            continue
        msg = await recv_json(ws)
        e_results[label] = msg
        if msg is None:
            print(f"  [--]   {label:8s} 未收到消息 (超时)")
        elif isinstance(msg, dict) and msg.get("type") == "PROPOSAL_CREATED":
            e_broadcast_count += 1
            print(f"  [OK]   {label:8s} 收到 PROPOSAL_CREATED 广播")
        elif isinstance(msg, dict) and msg.get("type") == "ERROR":
            event = msg.get("payload", {}).get("event", "")
            reason = msg.get("payload", {}).get("reason", "")
            print(f"  [REJ]  {label:8s} 收到 ERROR: event={event}, reason={reason}")
        elif isinstance(msg, dict) and msg.get("_closed"):
            print(f"  [CLS]  {label:8s} 连接已关闭 (code={msg.get('code')})")
        else:
            print(f"  [??]   {label:8s} 收到: {msg}")
    results["E_proposal"] = {
        "broadcast_count": e_broadcast_count,
        "details": e_results,
    }

    # ================================================================
    # F. 读者发送 STATE_CHANGE — 应被拒绝
    # ================================================================
    print()
    print("=" * 70)
    print("F. 读者发送 STATE_CHANGE — 应被拒绝 (reader 无权限)")
    print("=" * 70)
    await drain_all(clients)

    state_msg = {"type": "STATE_CHANGE", "to_state": "discussion"}
    try:
        await send_json(clients["reader"], state_msg)
        print("  [INFO] reader 已发送 STATE_CHANGE")
    except Exception as e:
        print(f"  [FAIL] reader 发送失败: {e}")

    f_results = {}
    f_rejected = False
    reader_msg = await recv_json(clients["reader"])
    f_results["reader"] = reader_msg
    if isinstance(reader_msg, dict) and reader_msg.get("type") == "ERROR":
        f_rejected = True
        reason = reader_msg.get("payload", {}).get("reason", "")
        print(f"  [OK]   reader    收到 ERROR 拒绝: {reason}")
    elif isinstance(reader_msg, dict) and reader_msg.get("_closed"):
        f_rejected = True
        print(
            f"  [OK]   reader    连接被关闭 (code={reader_msg.get('code')}, "
            f"reason={reader_msg.get('reason')})"
        )
    elif isinstance(reader_msg, dict) and reader_msg.get("type") == "STATE_CHANGE":
        print("  [FAIL] reader    收到 STATE_CHANGE 广播 (期望被拒绝!)")
    elif reader_msg is None:
        # 连接可能已被关闭，检查状态
        if not is_open(clients.get("reader")):
            f_rejected = True
            print("  [OK]   reader    连接已被服务器关闭 (符合拒绝预期)")
        else:
            print("  [--]   reader    未收到消息 (超时)")
    else:
        print(f"  [??]   reader    收到: {reader_msg}")

    # 检查 reader 连接是否被关闭
    reader_closed = "reader" in clients and not is_open(clients["reader"])
    if reader_closed and not f_rejected:
        f_rejected = True
        print("  [OK]   reader    连接已被服务器关闭 (符合拒绝预期)")

    # 检查其他客户端是否未收到 STATE_CHANGE 广播
    await asyncio.sleep(0.5)
    for label in ["owner", "editor", "reviewer"]:
        ws = clients.get(label)
        if ws is None or not is_open(ws):
            continue
        msg = await recv_json(ws, timeout=1.0)
        f_results[label] = msg
        if msg is None:
            print(f"  [OK]   {label:8s} 未收到广播 (符合预期)")
        elif isinstance(msg, dict) and msg.get("payload", {}).get("event") == "user_left":
            print(f"  [LEFT] {label:8s} 收到 user_left 通知 (reader 离开)")
        elif isinstance(msg, dict) and msg.get("type") == "STATE_CHANGE":
            print(f"  [FAIL] {label:8s} 收到 STATE_CHANGE 广播 (期望不广播!)")
        else:
            print(f"  [??]   {label:8s} 收到: {msg}")
    results["F_reader_rejected"] = {"rejected": f_rejected, "details": f_results}

    # ================================================================
    # G. 所有者发送 STATE_CHANGE — 应被接受
    # ================================================================
    print()
    print("=" * 70)
    print("G. 所有者发送 STATE_CHANGE — 应被接受")
    print("=" * 70)
    await drain_all(clients)

    owner_state_msg = {"type": "STATE_CHANGE", "to_state": "discussion"}
    try:
        await send_json(clients["owner"], owner_state_msg)
        print("  [INFO] owner 已发送 STATE_CHANGE")
    except Exception as e:
        print(f"  [FAIL] owner 发送失败: {e}")

    g_results = {}
    g_accepted = False
    g_broadcast_count = 0
    for label in ["owner", "editor", "reviewer", "reader"]:
        ws = clients.get(label)
        if ws is None or not is_open(ws):
            print(f"  [SKIP] {label:8s} 连接已断开，跳过")
            continue
        msg = await recv_json(ws)
        g_results[label] = msg
        msg_type = msg.get("type", "") if isinstance(msg, dict) else ""
        payload_event = (
            msg.get("payload", {}).get("event", "") if isinstance(msg, dict) else ""
        )
        if msg_type == "STATE_CHANGE" and payload_event != "user_left":
            g_broadcast_count += 1
            print(f"  [OK]   {label:8s} 收到 STATE_CHANGE 广播")
        elif msg_type == "STATE_CHANGE" and payload_event == "user_left":
            print(f"  [LEFT] {label:8s} 收到 user_left 通知")
        elif msg_type == "ERROR":
            reason = msg.get("payload", {}).get("reason", "")
            print(f"  [REJ]  {label:8s} 收到 ERROR: {reason}")
        elif isinstance(msg, dict) and msg.get("_closed"):
            print(f"  [CLS]  {label:8s} 连接已关闭 (code={msg.get('code')})")
        elif msg is None:
            # owner 未收到 ERROR = 权限通过 = accepted
            if label == "owner":
                g_accepted = True
                print(f"  [OK]   {label:8s} 未收到 ERROR (权限通过，已接受)")
            else:
                print(f"  [--]   {label:8s} 未收到消息 (超时)")
        else:
            print(f"  [??]   {label:8s} 收到: {msg}")

    # 如果 owner 没有收到 ERROR，说明权限校验通过
    owner_resp = g_results.get("owner")
    if isinstance(owner_resp, dict) and owner_resp.get("type") == "ERROR":
        g_accepted = False
    elif owner_resp is None:
        g_accepted = True

    results["G_owner_state"] = {
        "accepted": g_accepted,
        "broadcast_count": g_broadcast_count,
        "details": g_results,
    }

    # ================================================================
    # H. 速率限制测试 — 70 条消息
    # ================================================================
    print()
    print("=" * 70)
    print("H. 速率限制测试 — 发送 70 条消息")
    print("=" * 70)

    # 使用全新连接进行速率限制测试
    rate_uri = f"{BASE_WS}/api/collab/ws/{doc_id}?token={tokens['owner']}"
    try:
        ws_rate = await websockets.connect(rate_uri)
        print("  [INFO] 已建立全新连接用于速率限制测试")
    except Exception as e:
        print(f"  [FAIL] 无法建立测试连接: {e}")
        ws_rate = None

    h_results = {}
    if ws_rate:
        await asyncio.sleep(0.3)
        await drain(ws_rate)

        total_sent = 70
        # 使用小写 ping 以获得 pong 响应，便于统计成功数
        ping_msg = {"type": "ping"}

        print(f"  [INFO] 快速发送 {total_sent} 条 PING 消息...")
        for i in range(total_sent):
            try:
                await send_json(ws_rate, ping_msg)
            except Exception as e:
                print(f"  [FAIL] 发送第 {i + 1} 条失败: {e}")
                break

        # 等待服务器处理
        await asyncio.sleep(1.5)

        # 收集所有响应
        pongs = 0
        rate_errors = 0
        other_msgs = 0
        first_rate_limited_at = None

        for i in range(total_sent):
            msg = await recv_json(ws_rate, timeout=1.0)
            if msg is None:
                break
            if isinstance(msg, dict) and msg.get("type") == "pong":
                pongs += 1
            elif (
                isinstance(msg, dict)
                and msg.get("type") == "ERROR"
                and msg.get("payload", {}).get("event") == "rate_limited"
            ):
                rate_errors += 1
                if first_rate_limited_at is None:
                    first_rate_limited_at = pongs + 1
            else:
                other_msgs += 1

        print(f"  [INFO] 发送消息总数: {total_sent}")
        print(f"  [OK]   PONG 响应 (通过): {pongs}")
        print(f"  [OK]   ERROR 响应 (限流): {rate_errors}")
        if other_msgs:
            print(f"  [WARN] 其他消息: {other_msgs}")
        if first_rate_limited_at:
            print(
                f"  [OK]   首次限流出现在第 {first_rate_limited_at} 条响应"
                f" (期望: 61)"
            )

        h_results = {
            "sent": total_sent,
            "pong": pongs,
            "rate_limited": rate_errors,
            "other": other_msgs,
            "first_rate_limited_at": first_rate_limited_at,
        }
        results["H_rate_limit"] = h_results

        try:
            await ws_rate.close()
        except Exception:
            pass

    # ================================================================
    # I. 汇总报告
    # ================================================================
    print()
    print("=" * 70)
    print("I. 测试汇总报告")
    print("=" * 70)

    # 构建汇总表
    summary_rows = []

    # A. 登录
    login_ok = sum(1 for v in results.get("A_login", {}).values() if v)
    summary_rows.append(
        ("A", "登录 4 个用户", "4/4 登录成功", f"{login_ok}/4 登录成功",
         "PASS" if login_ok == 4 else "FAIL")
    )

    # B. 文档
    doc_found = results.get("B_doc_id")
    summary_rows.append(
        ("B", "查找种子文档", "doc_id 找到", str(doc_found) if doc_found else "未找到",
         "PASS" if doc_found else "FAIL")
    )

    # C. 连接
    conn_ok = sum(1 for v in results.get("C_connect", {}).values() if v)
    summary_rows.append(
        ("C", "连接 4 个 WS 客户端", "4 个连接", f"{conn_ok} 个连接",
         "PASS" if conn_ok == 4 else "FAIL")
    )

    # D. 验证
    d_data = results.get("D_verify", {})
    d_conn = d_data.get("connected", 0)
    summary_rows.append(
        ("D", "验证所有连接", "4/4 已连接", f"{d_conn}/4 已连接",
         "PASS" if d_conn == 4 else "FAIL")
    )

    # E. PROPOSAL_CREATED 广播
    e_data = results.get("E_proposal", {})
    e_bcast = e_data.get("broadcast_count", 0)
    summary_rows.append(
        ("E", "editor 发送 PROPOSAL_CREATED", "广播给其他客户端",
         f"{e_bcast} 个客户端收到广播",
         "PASS" if e_bcast > 0 else "FAIL")
    )

    # F. Reader 被拒绝
    f_data = results.get("F_reader_rejected", {})
    f_rej = f_data.get("rejected", False)
    summary_rows.append(
        ("F", "reader 发送 STATE_CHANGE", "被拒绝 (ERROR)",
         "已拒绝" if f_rej else "未被拒绝",
         "PASS" if f_rej else "FAIL")
    )

    # G. Owner 被接受
    g_data = results.get("G_owner_state", {})
    g_acc = g_data.get("accepted", False)
    g_bcast = g_data.get("broadcast_count", 0)
    g_desc = f"已接受, 广播={g_bcast}"
    summary_rows.append(
        ("G", "owner 发送 STATE_CHANGE", "被接受并广播",
         g_desc,
         "PASS" if g_acc and g_bcast > 0 else ("WARN" if g_acc else "FAIL"))
    )

    # H. 速率限制
    h_data = results.get("H_rate_limit", {})
    if h_data:
        h_pong = h_data.get("pong", 0)
        h_limit = h_data.get("rate_limited", 0)
        h_first = h_data.get("first_rate_limited_at", "N/A")
        summary_rows.append(
            ("H", "速率限制 (70 条消息)", "60 通过 + 10 限流",
             f"{h_pong} 通过 + {h_limit} 限流 (首次: {h_first})",
             "PASS" if h_pong <= 60 and h_limit >= 1 else "FAIL")
        )
    else:
        summary_rows.append(
            ("H", "速率限制 (70 条消息)", "60 通过 + 10 限流",
             "未执行", "FAIL")
        )

    # 打印表格
    print()
    header = f"{'测试':<5} {'描述':<28} {'期望':<22} {'实际':<32} {'结果':<6}"
    print(header)
    print("-" * len(header))
    for row in summary_rows:
        test, desc, expected, actual, verdict = row
        print(f"{test:<5} {desc:<28} {expected:<22} {actual:<32} {verdict:<6}")
    print("-" * len(header))

    # 统计
    pass_count = sum(1 for r in summary_rows if r[4] == "PASS")
    fail_count = sum(1 for r in summary_rows if r[4] == "FAIL")
    warn_count = sum(1 for r in summary_rows if r[4] == "WARN")
    print(f"\n总计: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")

    # 详细信息
    print("\n[连接状态]")
    for label in ["owner", "editor", "reviewer", "reader"]:
        login_s = "登录成功" if label in tokens else "登录失败"
        ws_s = "已连接" if label in clients and is_open(clients[label]) else "未连接"
        print(f"  {label:8s}: {login_s}, WebSocket {ws_s}")

    print("\n[E. PROPOSAL_CREATED 广播详情]")
    for label, msg in e_results.items():
        if isinstance(msg, dict):
            t = msg.get("type", "")
            if t == "PROPOSAL_CREATED":
                print(f"  {label:8s}: 收到广播")
            elif t == "ERROR":
                print(f"  {label:8s}: ERROR - {msg.get('payload', {}).get('reason', '')}")
            elif msg.get("_closed"):
                print(f"  {label:8s}: 连接关闭 (code={msg.get('code')})")
            else:
                print(f"  {label:8s}: {t or '无消息'}")
        elif msg is None:
            print(f"  {label:8s}: 未收到消息 (超时)")
        else:
            print(f"  {label:8s}: {msg}")

    print("\n[F. Reader STATE_CHANGE 拒绝详情]")
    reader_resp = f_results.get("reader")
    if isinstance(reader_resp, dict):
        if reader_resp.get("type") == "ERROR":
            print(f"  reader: 已拒绝 - {reader_resp.get('payload', {}).get('reason', '')}")
        elif reader_resp.get("_closed"):
            print(f"  reader: 连接关闭 (code={reader_resp.get('code')}, reason={reader_resp.get('reason')})")
        else:
            print(f"  reader: {reader_resp}")
    elif reader_resp is None:
        print("  reader: 未收到消息 (可能连接已关闭)")

    print("\n[G. Owner STATE_CHANGE 接受详情]")
    for label, msg in g_results.items():
        if isinstance(msg, dict):
            t = msg.get("type", "")
            if t == "STATE_CHANGE":
                event = msg.get("payload", {}).get("event", "")
                print(f"  {label:8s}: 收到 STATE_CHANGE (event={event})")
            elif t == "ERROR":
                print(f"  {label:8s}: ERROR - {msg.get('payload', {}).get('reason', '')}")
            elif msg.get("_closed"):
                print(f"  {label:8s}: 连接关闭 (code={msg.get('code')})")
            else:
                print(f"  {label:8s}: {t or '无消息'}")
        elif msg is None:
            status = "已接受 (无 ERROR)" if label == "owner" else "未收到消息 (超时)"
            print(f"  {label:8s}: {status}")

    print("\n[H. 速率限制详情]")
    if h_data:
        print(f"  发送消息: {h_data.get('sent', 0)} 条")
        print(f"  PONG (通过): {h_data.get('pong', 0)} 条")
        print(f"  ERROR (限流): {h_data.get('rate_limited', 0)} 条")
        print(f"  首次限流: 第 {h_data.get('first_rate_limited_at', 'N/A')} 条响应")
        if h_data.get("pong", 0) <= 60 and h_data.get("rate_limited", 0) >= 1:
            print("  结论: 速率限制生效 (限制: 60 条/分钟)")
        else:
            print("  结论: 速率限制结果异常")

    print("\n" + "=" * 70)
    print("测试完成。")
    print("=" * 70)

    # 清理连接
    for ws in clients.values():
        try:
            await ws.close()
        except Exception:
            pass

    return results


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ABORT] 用户中断")
        sys.exit(1)
