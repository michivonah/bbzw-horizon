# Stage 1: Build
FROM node:22-alpine as build

# Setze den Arbeitsordner
WORKDIR /app/

# Installiere git, um das Repository klonen zu können
RUN apk update && apk add git

# Klone das GitHub-Repository
RUN git clone https://github.com/bjgedeon/Frontend-M241-245.git .

# Installiere Abhängigkeiten
RUN npm install

# Erstelle die Produktionsversion
RUN npm run build

# Stage 2: Serve
FROM node:22-alpine as serve

# Installiere Serve um statische Dateien zu bedienen
RUN npm install -g serve

# Setze den Arbeitsordner
WORKDIR /app/

# Kopiere die gebauten Dateien vom vorherigen Build
COPY --from=build /app/dist ./dist

# Exponiere den Port
EXPOSE 3000

# Kommando zum Ausführen des Servers
CMD ["serve", "-s", "dist", "-l", "3000"]