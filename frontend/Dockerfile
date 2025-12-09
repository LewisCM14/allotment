# Build stage
FROM node:22.14.0-slim AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --ignore-scripts

# Copy source code and config files
COPY src/ ./src/
COPY public/ ./public/
COPY config/vite.config.ts ./config/vite.config.ts
COPY tsconfig.json ./
COPY tsconfig.app.json ./
COPY tsconfig.node.json ./
COPY components.json ./
COPY index.html ./

# Build the application
RUN npm run build

# Production stage (non-root nginx)
FROM nginxinc/nginx-unprivileged:stable

# Switch to root to adjust permissions during build, will drop back to non-root
USER root

# Copy built assets from build stage (initial copy without specific permissions)
COPY --from=build /app/dist /usr/share/nginx/html
# Set ownership and remove all write permissions: files=0444 (r--r--r--), dirs=0555 (r-xr-xr-x)
RUN chown -R 101:101 /usr/share/nginx/html && \
    find /usr/share/nginx/html -type f -exec chmod 0444 {} + && \
    find /usr/share/nginx/html -type d -exec chmod 0555 {} + && \
    mkdir -p /usr/share/nginx/html/runtime && \
    chown 101:101 /usr/share/nginx/html/runtime && \
    chmod 0775 /usr/share/nginx/html/runtime

# Ensure nginx can write generated config at runtime, copy config & entrypoint, set permissions (merged)
COPY nginx.conf /etc/nginx/conf.d/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chown -R 101:101 /etc/nginx/conf.d && \
    chmod +x /docker-entrypoint.sh && \
    chown 101:101 /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Add healthcheck (nginx-unprivileged listens on 8080)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

## Expose unprivileged port
EXPOSE 8080

# Drop privileges back to image default non-root user
USER 101

# Start nginx (non-root)
CMD ["nginx", "-g", "daemon off;"]
