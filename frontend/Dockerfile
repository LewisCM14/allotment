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

# Production stage - use nginx with Brotli support for serving pre-compressed .br files
# hadolint ignore=DL3007
FROM fholzer/nginx-brotli:v1.26.2

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Set ownership of static files to nginx user
RUN chown -R nginx:nginx /usr/share/nginx/html

# Copy nginx config as a template
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Copy and set entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Set permissions for entrypoint and nginx config directory (merged for fewer layers)
# Create writable directories for nginx to run as non-root user
RUN chmod +x /docker-entrypoint.sh && \
    chown nginx:nginx /docker-entrypoint.sh && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    mkdir -p /tmp/nginx && \
    chown -R nginx:nginx /tmp/nginx /var/cache/nginx

# Switch to non-root user for security
USER nginx

ENTRYPOINT ["/docker-entrypoint.sh"]

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start nginx as non-root user, with PID file in writable location
CMD ["nginx", "-g", "daemon off; pid /tmp/nginx/nginx.pid;"]
