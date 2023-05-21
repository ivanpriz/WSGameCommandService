Online game with movement mechanic. 
You can move from cell to cell and can not collide with other players.
Currently has client in js and html and websocket server that does all the rendering and users management.
Further will separate server to several services (users, render, commands at least).

Setting up locally with docker-compose:
1) Pull latest Rabbit image
docker pull rabbitmq:management
2) Build commands_service image:
cd ${YOUR_COMMANDS_SERVER_DIR} & docker build -t commands_service .
