FROM node:22-alpine

RUN mkdir app
WORKDIR /app/

RUN apk update && apk add git
RUN git clone https://github.com/bjgedeon/Frontend-M241-245.git

WORKDIR /app/Frontend-M241-245

RUN npm install

EXPOSE 5173

CMD [ "npm", "run", "dev", "--", "--host", "0.0.0.0" ]

