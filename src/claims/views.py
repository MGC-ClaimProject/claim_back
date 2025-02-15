from rest_framework import status
from rest_framework.generics import get_object_or_404, ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from claims.models import Claim, AddDocument
from claims.serializers import ClaimSerializer, ClaimAddDocumentSerializer
from members.models import Member
from utils.fax_converter import convert_to_fax_tiff  # ✅ 팩스 변환 모듈 가져오기


# 🔹 로그인한 사용자의 모든 청구 리스트 조회 (UserClaimListView)
@extend_schema_view(
    get=extend_schema(
        operation_id="user_claim_list",
        summary="내 멤버들의 청구 리스트",
        description="로그인한 사용자가 보유한 모든 멤버들의 보험 청구 내역을 조회합니다.",
        responses={200: ClaimSerializer(many=True)}
    )
)
class ClaimListUserView(ListAPIView):
    serializer_class = ClaimSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        members = Member.objects.filter(user=user)
        return Claim.objects.filter(member__in=members)


# 🔹 특정 멤버의 청구 리스트 조회 및 새 청구 생성 (ClaimListCreateView)
@extend_schema_view(
    get=extend_schema(
        operation_id="member_claim_list",
        summary="특정 멤버의 청구 리스트 조회",
        description="특정 멤버의 보험 청구 리스트를 조회합니다.",
        responses={200: ClaimSerializer(many=True)}
    ),
    post=extend_schema(
        operation_id="create_member_claim",
        summary="특정 멤버의 청구 생성",
        description="특정 멤버에 대한 새로운 보험 청구를 생성합니다.",
        request=ClaimSerializer,
        responses={201: ClaimSerializer}
    )
)
class ClaimListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClaimSerializer

    def get_queryset(self):
        member_id = self.kwargs.get("pk")
        member = get_object_or_404(Member, pk=member_id)
        return Claim.objects.filter(member=member)

    def create(self, request, *args, **kwargs):
        member_id = self.kwargs.get("pk")
        member = get_object_or_404(Member, pk=member_id)

        data = request.data.copy()
        data["member"] = member.id
        bypass_duplicate_check = data.get("bypass_duplicate_check", False)  # ✅ KeyError 방지


        # ✅ 중복 체크
        existing_claim = Claim.objects.filter(
            member=member,
            incident_date=data.get("incident_date"),
            incident_type=data.get("incident_type"),
        ).first()

        # ✅ 중복이 존재하고 우회 플래그가 없으면 409 반환
        if existing_claim and not bypass_duplicate_check:
            serializer = self.get_serializer(existing_claim)
            return Response(
                {
                    "detail": "이미 동일한 사고 유형으로 접수된 청구가 존재합니다.",
                    "existing_claim": serializer.data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ✅ 유효성 검사 전 디버깅 로그 추가
        print("📤 [DEBUG] 백엔드에서 받는 데이터:", data)

        # ✅ 중복 확인을 우회하거나 기존 청구가 없을 경우 정상 생성
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)  # 🔍 여기가 실패하는지 확인
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)



# 🔹 특정 청구 조회, 수정, 삭제 (ClaimDetailDestroyView)
@extend_schema_view(
    get=extend_schema(
        operation_id="get_claim_detail",
        summary="보험 청구 상세 조회",
        description="특정 보험 청구 정보를 조회합니다.",
        responses={200: ClaimSerializer}
    ),
    put=extend_schema(
        operation_id="update_claim_detail",
        summary="보험 청구 전체 업데이트",
        description="보험 청구 정보를 전체 업데이트합니다.",
        request=ClaimSerializer,
        responses={200: ClaimSerializer}
    ),
    patch=extend_schema(
        operation_id="partial_update_claim",
        summary="보험 청구 부분 업데이트",
        description="보험 청구 정보를 부분 업데이트합니다.",
        request=ClaimSerializer,
        responses={200: ClaimSerializer}
    ),
    delete=extend_schema(
        operation_id="delete_claim",
        summary="보험 청구 삭제",
        description="특정 보험 청구를 삭제합니다.",
        responses={204: None}
    )
)
class ClaimDetailDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClaimSerializer

    def get_queryset(self):
        """특정 멤버의 특정 청구 정보를 가져오기 위한 쿼리셋"""
        member_id = self.kwargs.get("member_id")
        claim_id = self.kwargs.get("claim_id")
        return Claim.objects.filter(member__id=member_id, id=claim_id)

    def update(self, request, *args, **kwargs):
        """특정 청구 정보 업데이트"""
        partial = kwargs.pop("partial", False)  # PATCH 요청인지 확인
        instance = self.get_object()
        data = request.data.copy()

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """특정 청구 정보 삭제"""
        instance = self.get_object()
        instance.delete()
        return Response({"message": "보험 청구가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)



class ClaimAddDocumentConvertFaxView(ListCreateAPIView):
    """
    📌 특정 청구(Claim)의 여러 문서를 하나의 TIFF G3/G4 파일로 변환하여 저장하는 뷰
    """
    serializer_class = ClaimAddDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """ 특정 청구(Claim)에 저장된 문서 조회 """
        claim_id = self.kwargs.get("claim_id")
        return AddDocument.objects.filter(claim_id=claim_id)

    def create(self, request, *args, **kwargs):
        claim_id = self.kwargs.get("claim_id")
        claim = get_object_or_404(Claim, id=claim_id)

        uploaded_files = request.FILES.getlist("documents")

        if not uploaded_files:
            return Response({"error": "📁 업로드할 파일을 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ 여러 개의 문서를 하나의 TIFF 파일로 변환
            merged_tiff_file = convert_to_fax_tiff(uploaded_files)

            # ✅ 기존 문서 삭제 (하나의 파일로 유지)
            AddDocument.objects.filter(claim=claim).delete()

            # ✅ 변환된 TIFF 파일을 `AddDocument`에 저장
            document_instance = AddDocument.objects.create(claim=claim)
            document_instance.document.save(f"{claim_id}_merged_fax.tiff", merged_tiff_file)

            return Response(
                {
                    "message": "📜 모든 문서가 하나의 TIFF 파일로 변환되어 저장되었습니다.",
                    "document_url": document_instance.document.url,  # ✅ 문서 URL 반환
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        """ ✅ 특정 청구(Claim)의 기존 문서 목록을 반환 """
        claim_id = self.kwargs.get("claim_id")
        documents = AddDocument.objects.filter(claim_id=claim_id)

        if not documents.exists():
            return Response({"message": "📂 저장된 문서가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        document_urls = [{"id": doc.id, "document_url": doc.document.url} for doc in documents]

        return Response({"documents": document_urls}, status=status.HTTP_200_OK)






class ClaimAddDocumentEditFaxView(RetrieveUpdateDestroyAPIView):
    """
    특정 청구(Claim)에 속한 문서 수정 및 삭제 뷰
    """
    serializer_class = ClaimAddDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 파일 업로드 지원

    def get_queryset(self):
        """ 특정 청구(Claim)에 속한 특정 문서를 조회 """
        claim_id = self.kwargs.get("claim_id")
        return AddDocument.objects.filter(claim_id=claim_id)

    def perform_update(self, serializer):
        """ 문서 업데이트 (수정 가능, TIFF 변환 옵션 추가) """
        instance = self.get_object()

        # ✅ 요청에서 팩스 변환 여부 확인 (기본값: False)
        is_fax_conversion = self.request.data.get("is_fax_conversion", False)

        uploaded_file = self.request.FILES.get("document")
        if not uploaded_file:
            return Response({"error": "업로드할 파일이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ 사용자가 TIFF 변환을 원하면 변환 후 저장
            if is_fax_conversion:
                converted_file = convert_to_fax_tiff(uploaded_file)  # 🔹 팩스 TIFF 변환
                instance.document.delete()  # 기존 파일 삭제
                instance.document = converted_file
            else:
                # ✅ TIFF 변환 없이 원본 파일 그대로 저장
                instance.document.delete()  # 기존 파일 삭제
                instance.document = uploaded_file

            instance.save()
            return Response({"message": "📄 문서가 성공적으로 업데이트되었습니다."}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        """ 문서 삭제 """
        instance.document.delete()  # 기존 파일 삭제
        instance.delete()
        return Response({"detail": "문서가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
