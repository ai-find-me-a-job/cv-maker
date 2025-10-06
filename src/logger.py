import logging


def setup_default_logger():
    # Create a logger
    logger = logging.getLogger("default")
    logger.setLevel(logging.DEBUG)  # Set the minimum level for this logger

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Set the minimum level for console output
    # Attach formatters to handlers
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    file_handler = logging.FileHandler("app.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


default_logger = setup_default_logger()
