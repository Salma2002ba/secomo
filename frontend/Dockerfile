# Étape 1 : build de l'application React avec Vite
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Adresses de l'API injectées au moment du build (Vite les inscrit dans le bundle)
ARG VITE_API_BASE=http://localhost:8000
ARG VITE_WS_BASE=ws://localhost:8000
ENV VITE_API_BASE=${VITE_API_BASE} VITE_WS_BASE=${VITE_WS_BASE}
RUN npm run build

# Étape 2 : fichiers statiques servis par Nginx
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
