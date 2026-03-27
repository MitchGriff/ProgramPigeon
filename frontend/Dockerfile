# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# --- Runtime stage: serve the built app with nginx ---
FROM nginx:alpine

# Copy built React app into nginx's serve directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config (handles React Router client-side routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
