import logging

import requests
from common.exceptions import UnauthorizedException
from common.logging_config import logger
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers.user_serializers import UserSerializer

logger = logging.getLogger("custom_api_logger")


class KakaoLoginCallbackView(APIView):
    """카카오에서 받은 인가 코드로 로그인 처리"""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """✅ GET 요청으로 받은 인가 코드 처리"""
        code = request.GET.get("code")
        return self.handle_kakao_login(code)

    def post(self, request, *args, **kwargs):
        """✅ POST 요청으로 받은 인가 코드 처리"""
        code = request.data.get("code")
        return self.handle_kakao_login(code)

    def handle_kakao_login(self, code):
        """✅ 카카오 로그인 처리 공통 함수"""
        if not code:
            return Response(
                {"detail": "인가 코드가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger.debug(f"카카오 로그인 요청 - 받은 코드: {code}")

            # ✅ 1. 카카오에서 액세스 토큰 요청
            kakao_access_token = self._get_kakao_access_token(code)

            # ✅ 2. 카카오에서 사용자 정보 가져오기
            user_info = self._get_kakao_user_info(kakao_access_token)
            email = user_info.get("email")

            # ✅ 3. 유저 확인 및 생성
            user, created = User.objects.get_or_create(email=email)

            # ✅ 4. JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # ✅ 5. 응답 데이터 구성
            response_data = {
                "access_token": access_token,
                "user": UserSerializer(user).data,
            }

            response = Response(response_data, status=201 if created else 200)

            # ✅ 리프레시 토큰을 `Set-Cookie` 헤더에 포함
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
                path="/",
            )

            return response  # ✅ `POST` 방식으로 응답

        except Exception as e:
            logger.error(f"카카오 로그인 처리 중 오류 발생: {str(e)}")
            return Response(
                {"detail": "카카오 로그인 처리 중 오류 발생", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_kakao_access_token(self, code):
        """✅ 카카오에서 액세스 토큰 요청"""
        token_url = "https://kauth.kakao.com/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_CALLBACK_URL,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(token_url, data=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"카카오 액세스 토큰 요청 실패: {response.json()}")
            return None

        return response.json().get("access_token")

    def _get_kakao_user_info(self, access_token):
        """✅ 카카오에서 사용자 정보 가져오기"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:
            raise Exception("카카오에서 사용자 정보를 가져오는 데 실패했습니다.")

        data = response.json()
        kakao_account = data.get("kakao_account", {})
        return {"email": kakao_account.get("email")}


class RefreshAccessTokenAPIView(APIView):
    """리프레시 토큰을 이용한 Access Token 갱신 API View"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(
                "리프레시 토큰이 누락되었습니다.", code="MISSING_REFRESH_TOKEN"
            )

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.get("user_id")
            user = User.objects.get(id=user_id)

            new_access_token = str(refresh.access_token)

            response_data = {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": refresh.access_token.payload["exp"],
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except (User.DoesNotExist, TokenError):
            logger.error("리프레시 토큰이 유효하지 않음.")
            raise UnauthorizedException(
                "유효하지 않은 리프레시 토큰입니다.", code="INVALID_REFRESH_TOKEN"
            )


class LogoutView(APIView):
    """사용자 로그아웃 처리 View"""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Oauth"],
        summary="사용자 로그아웃",
        responses={200: {"type": "object", "description": "로그아웃 성공"}},
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(
                "리프레시 토큰이 누락되었습니다.", code="MISSING_REFRESH_TOKEN"
            )

        try:
            token = RefreshToken(refresh_token)

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

        except TokenError:
            logger.error("리프레시 토큰 블랙리스트 처리 중 오류 발생")
            raise UnauthorizedException(
                "유효하지 않은 리프레시 토큰입니다.", code="INVALID_REFRESH_TOKEN"
            )

        response = Response(
            {"detail": "로그아웃에 성공했습니다."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("refresh_token")
        return response
