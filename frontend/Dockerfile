# Stage 1: Build React static bundle with Node.js
FROM node:18-alpine AS build

WORKDIR /app

# Install npm dependencies
COPY package*.json ./
RUN npm install

# Copy frontend source code and compile Vite bundle
COPY . .
RUN npm run build

# Stage 2: Serve static files with Nginx
FROM nginx:alpine

# Copy compiled assets from Stage 1 into Nginx default root
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx configuration file for SPA routing and API proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
