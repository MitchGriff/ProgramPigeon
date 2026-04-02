# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# --- Runtime stage: serve with nginx, injecting backend URL at startup ---
FROM nginx:alpine

# gettext provides envsubst, used to inject BACKEND_INTERNAL_URL into nginx config at startup
RUN apk add --no-cache gettext

# Copy built React app into nginx's serve directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config template — backend URL is substituted at container startup
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

EXPOSE 80

# At startup: substitute env vars into the nginx config template, then start nginx
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_INTERNAL_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
