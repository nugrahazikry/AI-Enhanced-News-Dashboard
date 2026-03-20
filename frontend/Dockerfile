# ── Frontend Dockerfile ──────────────────────────────────────────────────────
# Build context: prod_v1/ (project root)
# Run:  docker build -f frontend/Dockerfile -t news-frontend .
# ─────────────────────────────────────────────────────────────────────────────
FROM nginx:stable-alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Serve static assets at /static/ inside the container
COPY frontend/static/ /usr/share/nginx/html/static/

# Custom Nginx config (proxies everything else to backend)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
