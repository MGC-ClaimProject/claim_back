import logging
import requests
from django.shortcuts import redirect
from common.exceptions import UnauthorizedException
from common.logging_config import logger
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from members.models import Member
from users.models import User
from users.serializers.oauth_serializers import SocialLoginSerializer, KakaoAuthCodeSerializer, RefreshTokenSerializer

logger = logging.getLogger("custom_api_logger")

@extend_schema(tags=["Oauth"])
class KakaoLoginCallbackView(APIView):
    """✅ 카카오 로그인 콜백 API"""
    permission_classes = [AllowAny]
    serializer_class = KakaoAuthCodeSerializer

    def get(self, request, *args, **kwargs):
        """✅ 카카오 로그인 후 프론트엔드로 리다이렉트"""
        code = request.GET.get("code")
        frontend_url = f"{settings.FRONTEND_CALLBACK_URL}{code}"
        return redirect(frontend_url)

    def post(self, request, *args, **kwargs):
        """✅ 프론트에서 받은 인가 코드로 카카오에 액세스 토큰 요청"""
        serializer = KakaoAuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_data = serializer.save()

        # ✅ 유저가 새로 생성된 경우 201 코드 반환
        user_created = auth_data["user_created"]
        status_code = status.HTTP_201_CREATED if user_created else status.HTTP_200_OK
        user_info = Member.objects.first()

        # ✅ 응답 객체 생성
        response = Response(
            {
                "access_token": auth_data["access_token"],
                "user": {
                    "id":auth_data["user"]["id"],  # 기존 user 정보
                    "use_name": user_info.name,  # 추가된 member 정보
                    "member_id": user_info.id,
                },
            },
            status=status_code,
        )

        # ✅ 리프레시 토큰을 HttpOnly 쿠키로 설정
        response.set_cookie(
            key="refresh_token",
            value=auth_data["refresh_token"],
            httponly=False,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # ✅ 7일
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

        if not kakao_id or not email:
            raise ValueError("카카오 사용자 정보를 가져올 수 없습니다.")

        # ✅ SocialLoginSerializer를 활용하여 유저 생성 또는 업데이트
        serializer = SocialLoginSerializer(data={"email": email})
        serializer.is_valid(raise_exception=True)

        user = serializer.save(social_kakao_id=kakao_id)
        return user


@extend_schema(tags=["Oauth"])
class RefreshAccessTokenAPIView(APIView):
    """리프레시 토큰을 이용한 Access Token 갱신 API View"""
    serializer_class = RefreshTokenSerializer
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
    permission_classes = (IsAuthenticated,)
    serializer_class = SocialLoginSerializer

    @extend_schema(
        tags=["Oauth"],
        summary="사용자 로그아웃",
        responses={200: {"type": "object", "description": "로그아웃 성공"}},
    )
    def post(self, request, *args, **kwargs):
        access_token = request.headers.get("Authorization")
        if not access_token:
            raise UnauthorizedException("액세스 토큰이 누락되었습니다.", code="MISSING_ACCESS_TOKEN")

        # ✅ 액세스 토큰에서 사용자 ID 추출
        try:
            access_token = access_token.split(" ")[1]  # "Bearer <token>"에서 토큰 부분만 추출
            decoded_access_token = AccessToken(access_token)
            user_id = decoded_access_token["user_id"]
        except Exception as e:
            logger.error(f"액세스 토큰 해독 실패: {e}")
            raise UnauthorizedException("유효하지 않은 액세스 토큰입니다.", code="INVALID_ACCESS_TOKEN")

        # ✅ 사용자와 연결된 리프레시 토큰 찾기
        from django.utils.timezone import now
        outstanding_tokens = OutstandingToken.objects.filter(user_id=user_id, expires_at__gt=now())

        if outstanding_tokens.exists():
            try:
                for token in outstanding_tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                    token.delete()  # ✅ DB에서 삭제
            except Exception as e:
                logger.error(f"리프레시 토큰 블랙리스트 처리 중 오류 발생: {e}")
                raise UnauthorizedException("리프레시 토큰 블랙리스트 처리 중 오류가 발생했습니다.", code="TOKEN_BLACKLIST_ERROR")

        # ✅ 프론트 쿠키에서도 리프레시 토큰 삭제
        response = Response({"detail": "로그아웃에 성공했습니다."}, status=status.HTTP_200_OK)

        return response