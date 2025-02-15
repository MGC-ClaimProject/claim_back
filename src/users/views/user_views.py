from drf_spectacular.utils import extend_schema, extend_schema_view
from members.models import Member
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from users.models import User
from users.serializers.user_serializers import UserSerializer


@extend_schema(tags=["User"])
@extend_schema_view(
    get=extend_schema(
        summary="내 정보 조회",
        description="로그인한 사용자의 정보를 조회합니다.",
        responses={200: UserSerializer},
    ),
    put=extend_schema(
        summary="내 정보 전체 업데이트",
        description="로그인한 사용자의 정보를 전체적으로 업데이트합니다. 모든 필드를 보내야 합니다.",
        request=UserSerializer,
        responses={200: UserSerializer},
    ),
    patch=extend_schema(
        summary="내 정보 부분 업데이트",
        description="로그인한 사용자의 정보를 부분적으로 업데이트합니다. 필요한 필드만 보낼 수 있습니다.",
        request=UserSerializer,
        responses={200: UserSerializer},
    ),
)
class UserAPIView(RetrieveUpdateAPIView):
    """로그인한 유저 정보를 반환하는 API"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # ✅ 로그인한 사용자만 접근 가능

    def get_object(self):
        """로그인한 사용자 정보 반환"""
        return self.request.user  # ✅ `user` 필드가 없으므로 직접 반환


# 회원탈퇴 요청시 사용하는 api
@extend_schema(tags=["User"])
class UserDeactivateAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def patch(self, request, *args, **kwargs):
        # 로그인한 사용자의 1번 멤버를 조회
        member = Member.objects.get(user=request.user, id=1)

        # 멤버 상태를 비활성화
        member.is_active = False
        member.save()
