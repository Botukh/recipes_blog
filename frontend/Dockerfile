FROM node:21.7.1-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/build ./build
CMD ["sh", "-c", "cp -r /app/build/. /static/ && echo 'Static files copied successfully'"]