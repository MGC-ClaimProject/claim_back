import logging
import requests
from django.shortcuts import redirect
from common.exceptions import UnauthorizedException
from common.logging_config import logger
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers.user_serializers import UserSerializer

logger = logging.getLogger("custom_api_logger")

class KakaoLoginCallbackView(APIView):
    """✅ 카카오 로그인 콜백 API"""
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        frontend_url = f"http://localhost:5173?code={code}"
        return redirect(frontend_url)

    def post(self, request, *args, **kwargs):
        """✅ 프론트에서 받은 인가 코드로 카카오에 액세스 토큰 요청"""
        code = request.data.get("code")
        logger.info(f"code: {code}")
        if not code:
            return Response({"detail": "인가 코드가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 카카오에서 액세스 토큰 요청
        access_token = self._get_kakao_access_token(code)
        if not access_token:
            return Response({"detail": "카카오 액세스 토큰 요청 실패"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 액세스 토큰을 이용해 사용자 정보 가져오기
        user = self._get_or_create_user(access_token)

        # ✅ JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # ✅ 응답 객체 생성
        response = Response({
            "access_token": access_token,
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)

        # ✅ 리프레시 토큰을 HttpOnly 쿠키로 설정
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # JavaScript에서 접근 불가 (보안 강화)
            secure=True,  # HTTPS에서만 전송 (로컬 개발 시 False)
            samesite="Lax",  # CORS 보안 설정
            max_age=7 * 24 * 60 * 60,  # 7일간 유효
        )

        return response

    def _get_kakao_access_token(self, code):
        """✅ 카카오 API에서 액세스 토큰 요청"""
        token_url = "https://kauth.kakao.com/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_CALLBACK_URL,  # ✅ 백엔드 주소 사용
            "code": code,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(token_url, data=payload, headers=headers)
        data = response.json()

        return data.get("access_token")

    def _get_or_create_user(self, access_token):
        """✅ 카카오 API에서 사용자 정보 가져와 유저 생성 또는 조회"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(user_info_url, headers=headers)
        user_data = response.json()

        kakao_id = user_data.get("id")
        email = user_data.get("kakao_account", {}).get("email", None)

        if not kakao_id:
            raise ValueError("카카오 사용자 정보를 가져올 수 없습니다.")

        # ✅ 기존 social_kakao_id가 있는 유저 확인
        user = User.objects.filter(social_kakao_id=kakao_id).first()
        if user:
            return user

        # ✅ 기존 이메일이 있는 유저 확인 후 social_kakao_id 업데이트
        user = User.objects.filter(email=email).first()
        if user:
            user.social_kakao_id = kakao_id
            user.save()
            return user

        # ✅ 새로운 유저 생성
        user = User.objects.create(
            email=email,
            social_kakao_id=kakao_id,
            is_active=True  # 기본 활성화
        )
        return user


@extend_schema(tags=["Oauth"])
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
