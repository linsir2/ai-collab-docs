FROM node:20-alpine

WORKDIR /app

# Deps first (layer caching)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
COPY contracts/ ./contracts/

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
