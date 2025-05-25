# Multi-stage Dockerfile for Olympian AI Frontend
# Optimized for production with caching and security

# Stage 1: Dependencies
FROM node:18-alpine as deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# Stage 2: Build
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev)
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 3: Production
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create nginx user and directories
RUN adduser -D -H -u 1000 -s /sbin/nologin nginx-user && \
    mkdir -p /var/cache/nginx /var/log/nginx && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Copy built files from builder
COPY --from=builder --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx-user:nginx-user nginx.conf /etc/nginx/nginx.conf

# Security headers and optimizations
RUN echo 'server_tokens off;' > /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Referrer-Policy "no-referrer-when-downgrade" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\''; style-src '\''self'\'' '\''unsafe-inline'\''; img-src '\''self'\'' data: https:; font-src '\''self'\''; connect-src '\''self'\'' http://backend:8000 ws://backend:8000;" always;' >> /etc/nginx/conf.d/security.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Expose ports
EXPOSE 80 443

# Run as non-root user
USER nginx-user

# Start nginx
CMD ["nginx", "-g", "daemon off;"]