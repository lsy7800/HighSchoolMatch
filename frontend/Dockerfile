# 前端镜像：多阶段构建。
# 1) node 构建 Vite 静态产物
# 2) nginx 托管 + 反代 /api、/health 到后端
FROM node:20-slim AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine

# 静态产物
COPY --from=build /app/dist /usr/share/nginx/html
# nginx 站点配置（反代后端 + SPA fallback）
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
