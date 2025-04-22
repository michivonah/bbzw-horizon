FROM node:22-alpine

RUN mkdir app
WORKDIR /app/

COPY git/ .

RUN npm install

EXPOSE 8080

CMD [ "npm", "run", "dev", "--", "--host", "0.0.0.0" ]