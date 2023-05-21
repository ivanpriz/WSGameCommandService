from environs import Env

env = Env()
env.read_env()


class Config:
    RABBITMQ_URI = env("RABBITMQ_URI")
    USERS_TO_CREATE_QUEUE = env("USERS_TO_CREATE_QUEUE")
    USERS_TO_DELETE_QUEUE = env("USERS_TO_DELETE_QUEUE")
    LOGGER_FORMAT_DEBUG = env("LOGGER_FORMAT_DEBUG", None)
    LOGGER_FORMAT_INFO = env("LOGGER_FORMAT_INFO", None)
