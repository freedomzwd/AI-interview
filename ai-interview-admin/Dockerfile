# 国内网络无法直连 Docker Hub，改用镜像加速器全路径
FROM docker.m.daocloud.io/library/node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
