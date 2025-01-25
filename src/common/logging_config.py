# common/logging_config.py
import logging

# 공통 로거 설정
logger = logging.getLogger("custom_api_logger")
logger.setLevel(logging.DEBUG)

# StreamHandler 설정
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# 포매터 설정
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

# 핸들러를 로거에 추가
if not logger.hasHandlers():
    logger.addHandler(stream_handler)
