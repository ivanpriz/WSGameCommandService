from environs import Env

env = Env()
env.read_env()


class Config:
    RABBITMQ_URI = env("RABBITMQ_URI")
    LOGGER_FORMAT_DEBUG = env("LOGGER_FORMAT_DEBUG", None)
    LOGGER_FORMAT_INFO = env("LOGGER_FORMAT_INFO", None)
    USERNAMES_FILE = env("USERNAMES_FILE")
    COLORS_FILE = env("COLORS_FILE")
