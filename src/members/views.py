from drf_spectacular.utils import extend_schema, extend_schema_view
from members.models import Member, Security
from members.serializers import MemberSerializer, SecuritySerializer
from rest_framework.generics import (CreateAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@extend_schema(tags=["Members"])
@extend_schema_view(
    post=extend_schema(
        summary="새 멤버 추가",
        description="로그인한 사용자의 멤버를 추가합니다.",
        request=MemberSerializer,
        responses={201: MemberSerializer},
    ),
)
class MemberListView(ListCreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """로그인한 사용자의 멤버들만 반환"""
        return Member.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """멤버 생성 시 로그인한 사용자와 연결"""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """회원가입 후 멤버 추가 요청"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # ✅ 응답을 직접 구성하여 회원가입 완료 후 프론트로 전달
        response_data = {
            "message": "회원가입이 완료되었습니다.",
            "member": serializer.data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Members"])
@extend_schema_view(
    get=extend_schema(
        summary="특정 멤버 조회",
        description="멤버 ID에 해당하는 특정 멤버 정보를 반환합니다.",
        responses={200: MemberSerializer},
    ),
    put=extend_schema(
        summary="특정 멤버 전체 업데이트",
        description="멤버 ID에 해당하는 멤버 정보를 전체적으로 업데이트합니다.",
        request=MemberSerializer,
        responses={200: MemberSerializer},
    ),
    patch=extend_schema(
        summary="특정 멤버 부분 업데이트",
        description="멤버 ID에 해당하는 멤버 정보를 부분적으로 업데이트합니다.",
        request=MemberSerializer,
        responses={200: MemberSerializer},
    ),
    delete=extend_schema(
        summary="특정 멤버 삭제",
        description="멤버 ID에 해당하는 멤버 정보를 삭제합니다.",
        responses={204: None},
    ),
)
class MemberDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MemberSerializer
    permission_classes = (IsAuthenticated,)  # 로그인된 사용자만 접근 가능

    def get_queryset(self):
        """
        로그인한 사용자의 특정 멤버를 반환
        """
        return Member.objects.filter(user=self.request.user)

    def get_object(self):
        """
        URL에 전달된 멤버 ID에 해당하는 객체 반환
        """
        return self.get_queryset().get(id=self.kwargs["pk"])


@extend_schema(tags=["Security"])
@extend_schema_view(
    post=extend_schema(
        summary="보안 정보 생성",
        description="특정 멤버와 연결된 보안 정보를 생성합니다.",
        request=SecuritySerializer,
        responses={201: SecuritySerializer},
    ),
)
class SecurityCreateView(CreateAPIView):
    serializer_class = SecuritySerializer
    permission_classes = (IsAuthenticated,)  # 로그인된 사용자만 접근 가능

    def perform_create(self, serializer):
        """
        보안 정보 생성 시 멤버와 연결
        """
        member_id = self.request.data.get("member")
        serializer.save(member_id=member_id)


@extend_schema(tags=["Security"])
@extend_schema_view(
    get=extend_schema(
        summary="보안 정보 조회",
        description="보안 정보 ID에 해당하는 보안 정보를 반환합니다.",
        responses={200: SecuritySerializer},
    ),
    put=extend_schema(
        summary="보안 정보 전체 업데이트",
        description="보안 정보를 전체적으로 업데이트합니다. 모든 필드를 보내야 합니다.",
        request=SecuritySerializer,
        responses={200: SecuritySerializer},
    ),
    patch=extend_schema(
        summary="보안 정보 부분 업데이트",
        description="보안 정보를 부분적으로 업데이트합니다. 필요한 필드만 보낼 수 있습니다.",
        request=SecuritySerializer,
        responses={200: SecuritySerializer},
    ),
    delete=extend_schema(
        summary="보안 정보 삭제",
        description="보안 정보를 삭제합니다.",
        responses={204: None},
    ),
)
class SecurityDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SecuritySerializer
    permission_classes = (IsAuthenticated,)  # 로그인된 사용자만 접근 가능

    def get_queryset(self):
        """
        로그인한 사용자와 연결된 보안 정보만 반환
        """
        return Security.objects.filter(member__user=self.request.user)

    def get_object(self):
        """
        URL에 전달된 보안 정보 ID에 해당하는 객체 반환
        """
        return self.get_queryset().get(id=self.kwargs["pk"])
