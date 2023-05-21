while getopts command:users:render:pull-git:pull-rabbit: flag
do
    case "${flag}" in
        command) COMMAND_SERVICE_PATH=${OPTARG};;
        users) USERS_SERVICE_PATH=${OPTARG};;
        render) RENDER_SERVICE_PATH=${OPTARG};;
        pull-git) NEED_GIT_PULL=true;;
        pull-rabbit) NEED_RABBIT_PULL=true;;
    esac
done

#if "$NEED_RABBIT_PULL"; then
#  docker pull rabbitmq:management
#fi
#if "$NEED_GIT_PULL"; then
#  git clone https://github.com/ivanpriz/WSGameCommandService.git $COMMAND_SERVICE_PATH
#  git clone https://github.com/ivanpriz/WSGameUsersService $USERS_SERVICE_PATH
#  git clone https://github.com/ivanpriz/WSGameRenderService.git $RENDER_SERVICE_PATH
#fi
USERS_SERVICE_PATH=$USERS_SERVICE_PATH COMMAND_SERVICE_PATH=$COMMAND_SERVICE_PATH RENDER_SERVICE_PATH=$RENDER_SERVICE_PATH docker-compose build
docker-compose up -d
