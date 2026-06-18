import http from "node:http";
import { URL } from "node:url";
import WebSocket from "ws";

const YJS_PORT = parseInt(process.env.YJS_PORT || "1234", 10);
const API_SERVER = process.env.API_SERVER || "http://localhost:8000";

const rooms = new Map<string, Set<WebSocket>>();

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", rooms: rooms.size }));
    return;
  }
  res.writeHead(404);
  res.end();
});

const wss = new WebSocket.Server({ server, maxPayload: 10 * 1024 * 1024 });

wss.on("connection", (ws, req) => {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  const docId = url.searchParams.get("docId") || "default";
  const userId = url.searchParams.get("userId") || "anonymous";

  if (!rooms.has(docId)) {
    rooms.set(docId, new Set());
  }
  rooms.get(docId)!.add(ws);

  broadcast(docId, { type: "user_joined", userId, docId }, ws);

  ws.on("message", (data) => {
    try {
      const message = JSON.parse(data.toString());
      broadcast(docId, { ...message, from: userId }, ws);
    } catch {
      broadcast(docId, data, ws);
    }
  });

  ws.on("close", () => {
    const room = rooms.get(docId);
    if (room) {
      room.delete(ws);
      if (room.size === 0) rooms.delete(docId);
    }
    broadcast(docId, { type: "user_left", userId, docId });
  });

  ws.on("error", () => {
    const room = rooms.get(docId);
    if (room) room.delete(ws);
  });
});

function broadcast(docId: string, message: any, exclude?: WebSocket) {
  const room = rooms.get(docId);
  if (!room) return;
  const payload = typeof message === "string" ? message : JSON.stringify(message);
  for (const client of room) {
    if (client !== exclude && client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  }
}

server.listen(YJS_PORT, () => {
  console.log(`Yjs collaboration server running on port ${YJS_PORT}`);
});
