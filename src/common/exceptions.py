# common/exceptions.py
from common.logging_config import logger
from rest_framework.exceptions import APIException


class CustomAPIException(APIException):
    """기본 Custom API Exception 클래스"""

    status_code = 400
    default_detail = "요청 처리 중 오류가 발생했습니다."
    default_code = "error"

    def __init__(self, detail=None, code=None, status_code=None):
        # 로깅 추가
        logger.error(f"Error occurred - Code: {code}, Detail: {detail}")

        # 상태 코드가 제공되면 재설정
        if status_code:
            self.status_code = status_code

        # 상세 메시지 설정
        self.detail = detail if detail else self.default_detail

        # 코드 설정
        self.code = code if code else self.default_code


class BadRequestException(CustomAPIException):
    """400 Bad Request"""

    status_code = 400
    default_detail = "잘못된 요청입니다."
    default_code = "bad_request"


class NotFoundException(CustomAPIException):
    """404 Not Found"""

    status_code = 404
    default_detail = "리소스를 찾을 수 없습니다."
    default_code = "not_found"


class InternalServerException(CustomAPIException):
    """500 Internal Server Error"""

    status_code = 500
    default_detail = "서버 내부 오류가 발생했습니다."
    default_code = "internal_server_error"


class UnauthorizedException(CustomAPIException):
    """401 Unauthorized"""

    status_code = 401
    default_detail = "인증이 필요합니다."
    default_code = "unauthorized"
