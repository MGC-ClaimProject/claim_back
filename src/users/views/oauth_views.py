import requests
from common.exceptions import (BadRequestException, InternalServerException,
                               UnauthorizedException)
from common.logging_config import logger
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers.oauth_serializers import (RefreshTokenSerializer,
                                                 SocialLoginSerializer)
from users.serializers.user_serializers import UserSerializer


# 소셜로그인 공통부분
class SocialLoginAPIView(APIView):
    """공통 소셜 로그인 처리 뷰"""

    @extend_schema(
        tags=["Oauth"],
        summary="소셜 로그인 처리",
        request={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "example": "AQAAAAAA1234",
                    "description": "소셜 인증 후 반환된 코드",
                },
                "state": {
                    "type": "string",
                    "example": "random-state",
                    "description": "CSRF 방지 상태값 (네이버 전용)",
                },
            },
            "required": ["code"],
        },
        responses={
            200: {"type": "object", "description": "로그인 성공"},
            400: {"type": "object", "description": "잘못된 요청"},
            500: {"type": "object", "description": "소셜 API 호출 실패"},
        },
    )
    # provider(공급자) -> naver, kakao, goggle
    def post(self, request, provider, *args, **kwargs):
        code = request.data.get("code")
        state = request.data.get("state")  # 네이버 인증용

        if not code:
            raise BadRequestException(
                "code 매개변수가 누락되었습니다.", code="missing_code"
            )

        try:
            # 소셜 액세스 토큰 가져오기
            access_token = self._get_social_access_token(provider, code, state)
            # 소셜 사용자 정보 가져오기
            user_info = self._get_social_user_info(provider, access_token)
            # 사용자 생성/업데이트
            serializer = SocialLoginSerializer(data=user_info)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # 사용자 정보 직렬화
            user_serializer = UserSerializer(user)

            # 응답 생성
            response_data = {
                "access_token": access_token,
                "user": user_serializer.data,
            }
            response = Response(response_data, status=status.HTTP_200_OK)

            # Refresh Token을 쿠키로 설정
            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=True,
                samesite="None",
            )
            return response
        except Exception as e:
            logger.error(f"{provider} 로그인 처리 중 오류 발생: {str(e)}")
            raise InternalServerException(
                f"{provider} 로그인 처리 중 오류가 발생했습니다.",
                code="social_login_failed",
            )

    def _get_social_access_token(self, provider, code, state=None):
        """소셜 제공자로부터 액세스 토큰 가져오기"""
        payload = {"grant_type": "authorization_code", "code": code}
        if provider == "naver":
            payload.update(
                {
                    "client_id": settings.NAVER_CLIENT_ID,
                    "client_secret": settings.NAVER_CLIENT_SECRET,
                    "state": state,
                }
            )
            token_url = settings.NAVER_TOKEN_URL
        elif provider == "kakao":
            payload.update(
                {
                    "client_id": settings.KAKAO_CLIENT_ID,
                    "redirect_uri": settings.KAKAO_CALLBACK_URL,
                }
            )
            token_url = settings.KAKAO_TOKEN_URL
        elif provider == "google":
            payload.update(
                {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                }
            )
            token_url = settings.GOOGLE_TOKEN_URL
        else:
            raise BadRequestException(
                "지원되지 않는 소셜 제공자입니다.", code="unsupported_provider"
            )

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(token_url, data=payload, headers=headers)
        if response.status_code != 200:
            raise InternalServerException(
                f"{provider}에서 액세스 토큰을 가져오는 데 실패했습니다.",
                code="token_fetch_failed",
            )
        return response.json().get("access_token")

    def _get_social_user_info(self, provider, access_token):
        """소셜 제공자로부터 사용자 정보 가져오기"""
        headers = {"Authorization": f"Bearer {access_token}"}
        if provider == "naver":
            user_info_url = settings.NAVER_USER_INFO_URL
        elif provider == "kakao":
            user_info_url = settings.KAKAO_USER_INFO_URL
        elif provider == "google":
            user_info_url = settings.GOOGLE_USER_INFO_URL
        else:
            raise BadRequestException(
                "지원되지 않는 소셜 제공자입니다.", code="unsupported_provider"
            )

        response = requests.get(user_info_url, headers=headers)
        if response.status_code != 200:
            raise InternalServerException(
                f"{provider}에서 사용자 정보를 가져오는 데 실패했습니다.",
                code="user_info_fetch_failed",
            )
        return self._parse_user_info(provider, response.json())

    def _parse_user_info(self, provider, data):
        """소셜 사용자 정보 파싱"""
        if provider == "naver":
            response_data = data.get("response", {})
            return {
                "email": response_data.get("email"),
            }
        elif provider == "kakao":
            kakao_account = data.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            return {
                "email": kakao_account.get("email"),
            }
        elif provider == "google":
            return {
                "email": data.get("email"),
            }
        else:
            raise BadRequestException(
                "지원되지 않는 소셜 제공자입니다.", code="unsupported_provider"
            )


class RefreshAccessTokenAPIView(APIView):
    """
    리프레시 토큰을 이용한 Access Token 갱신 API View.
    """

    @extend_schema(
        tags=["Oauth"],
        summary="리프레시 토큰으로 새로운 액세스 토큰 발급",
        responses={201: {"type": "object", "description": "새로운 액세스 토큰 발급"}},
    )
    def post(self, request, *args, **kwargs):
        # Step 1: Refresh Token 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(
                "리프레시 토큰이 누락되었습니다.", code="MISSING_REFRESH_TOKEN"
            )

        try:
            # Step 2: Refresh Token 검증
            serializer = RefreshTokenSerializer(data={"refresh_token": refresh_token})
            serializer.is_valid(raise_exception=True)

            refresh = RefreshToken(refresh_token)
            user_id = refresh.get("user_id")

            if not user_id:
                raise UnauthorizedException(
                    "리프레시 토큰에서 사용자 정보를 찾을 수 없습니다.",
                    code="INVALID_REFRESH_TOKEN",
                )

            # Step 3: 사용자 확인
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(
                    f"Access Token 갱신 중 오류 발생: User ID {user_id}에 해당하는 사용자가 없습니다."
                )
                raise UnauthorizedException(
                    "유효하지 않은 리프레시 토큰입니다. 사용자 정보를 찾을 수 없습니다.",
                    code="USER_NOT_FOUND",
                )

            # Step 4: 새로운 Access Token 생성
            refresh.set_jti()
            new_access_token = str(refresh.access_token)

            # Step 5: 응답 반환
            response_data = {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": refresh.access_token.payload["exp"],
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except TokenError:
            logger.error("리프레시 토큰이 유효하지 않음.")
            raise UnauthorizedException(
                "유효하지 않은 리프레시 토큰입니다.", code="INVALID_REFRESH_TOKEN"
            )
        except Exception as e:
            logger.error(f"Access Token 갱신 중 오류 발생: {str(e)}")
            raise InternalServerException(
                "Access Token 갱신 실패", code="ACCESS_TOKEN_REFRESH_FAILED"
            )


class LogoutView(APIView):
    """
    사용자 로그아웃 처리 View.
    """

    @extend_schema(
        tags=["Oauth"],
        summary="사용자 로그아웃",
        responses={200: {"type": "object", "description": "로그아웃 성공"}},
    )
    def post(self, request, *args, **kwargs):
        # Step 1: 쿠키에서 리프레시 토큰 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(
                detail="리프레시 토큰이 누락되었습니다.", code="MISSING_REFRESH_TOKEN"
            )

        try:
            # Step 2: 리프레시 토큰 객체 생성
            token = RefreshToken(refresh_token)

            # Step 3: OutstandingToken에서 삭제 및 BlacklistedToken으로 이동
            outstanding_token = OutstandingToken.objects.filter(
                jti=token["jti"]
            ).first()
            if outstanding_token:
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
                outstanding_token.delete()
            else:
                logger.warning(
                    "해당 리프레시 토큰을 OutstandingToken에서 찾을 수 없습니다."
                )

        except TokenError as e:
            logger.error(f"리프레시 토큰 블랙리스트 처리 중 오류 발생: {str(e)}")
            raise UnauthorizedException(
                detail="유효하지 않은 리프레시 토큰입니다.",
                code="INVALID_REFRESH_TOKEN",
            )

        # Step 4: 성공 응답 반환 및 쿠키 삭제
        response = Response(
            {"detail": "로그아웃에 성공했습니다."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("refresh_token")
        return response
