FROM node:24-alpine AS build

WORKDIR /app

RUN corepack enable

COPY . .

RUN yarn install --immutable
RUN yarn build

FROM caddy:2-alpine

COPY --from=build /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80
