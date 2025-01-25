from drf_spectacular.utils import extend_schema, extend_schema_view
from members.models import Member
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from users.serializers.user_serializers import MyInfoSerializer


@extend_schema(tags=["Users"])
@extend_schema_view(
    get=extend_schema(
        summary="내 정보 조회",
        description="로그인한 사용자의 멤버 ID 1번 정보를 조회합니다.",
        responses={200: MyInfoSerializer},
    ),
    put=extend_schema(
        summary="내 정보 전체 업데이트",
        description="로그인한 사용자의 멤버 정보를 전체적으로 업데이트합니다. 모든 필드를 보내야 합니다.",
        request=MyInfoSerializer,
        responses={200: MyInfoSerializer},
    ),
    patch=extend_schema(
        summary="내 정보 부분 업데이트",
        description="로그인한 사용자의 멤버 정보를 부분적으로 업데이트합니다. 필요한 필드만 보낼 수 있습니다.",
        request=MyInfoSerializer,
        responses={200: MyInfoSerializer},
    ),
)
class MyInfoAPIView(RetrieveUpdateAPIView):
    queryset = Member.objects.all()
    serializer_class = MyInfoSerializer
    # permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능
    permission_classes = [AllowAny]

    # 나의 정보는 로그인 유저의 가족멤버의 1번으로 고정되어있음.
    def get_object(self):
        return self.queryset.get(user=self.request.user).first()


@extend_schema(tags=["Users"])
@extend_schema_view(
    patch=extend_schema(
        summary="회원 탈퇴 요청",
        description="로그인한 사용자의 멤버 ID 1번 정보를 비활성화(탈퇴 처리)합니다.",
        request=None,  # 요청 바디가 필요 없는 경우 None으로 설정
        responses={200: {"type": "string", "example": "멤버가 비활성화되었습니다."}},
    )
)
# 회원탈퇴 요청시 사용하는 api
class MyInfoDeactivateAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        # 로그인한 사용자의 1번 멤버를 조회
        member = Member.objects.get(user=request.user, id=1)

        # 멤버 상태를 비활성화
        member.is_active = False
        member.save()
