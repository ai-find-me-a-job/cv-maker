import logging


def setup_default_logger():
    # Create a logger
    logger = logging.getLogger("default")
    logger.setLevel(logging.INFO)  # Set the minimum level for this logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Set the minimum level for console output

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Attach formatters to handlers
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)

    return logger


default_logger = setup_default_logger()
