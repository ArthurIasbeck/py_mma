from loguru import logger
logger.add("logs/py_mma.log", level="INFO", rotation="1MB")
