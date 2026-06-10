FROM node:20-alpine

WORKDIR /app

COPY yjs-server/package.json yjs-server/package-lock.json* ./
RUN npm install

COPY yjs-server/src/ ./src/

EXPOSE 1234
CMD ["npx", "tsx", "src/server.ts"]
