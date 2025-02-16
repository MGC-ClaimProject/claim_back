from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insurances.models import Insurance
from insurances.serializers import InsuranceSerializer
from members.models import Member


@extend_schema(tags=["Insurances"])
class InsuranceListView(ListCreateAPIView):
    """
    보험 리스트 조회 및 보험 생성 API
    """
    serializer_class = InsuranceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ✅ URL에서 `member_id` 가져오기
        member_id = self.kwargs.get("pk")
        member = get_object_or_404(Member, id=member_id)

        # ✅ 해당 멤버의 보험만 필터링
        return Insurance.objects.filter(member=member)

    def create(self, request, *args, **kwargs):
        # ✅ URL에서 `member_id` 가져오기
        member_id = self.kwargs.get("pk")
        member = get_object_or_404(Member, id=member_id)

        # ✅ 요청 데이터에 `member` 추가
        data = request.data.copy()
        data["member"] = member.id

        # ✅ 직렬화 후 저장
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)




@extend_schema(tags=["Insurances"])
class InsuranceDetailView(RetrieveUpdateDestroyAPIView):
    """
    보험 상세 조회, 수정 및 삭제 API
    """
    serializer_class = InsuranceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        insurance_id = self.kwargs.get("pk")
        return Insurance.objects.filter(id=insurance_id)


    def update(self, request, *args, **kwargs):
        """
        보험 정보를 수정하는 API (PUT/PATCH 지원)
        """
        insurance = self.get_object()
        serializer = self.get_serializer(insurance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        보험 정보를 삭제하는 API
        """
        insurance = self.get_object()
        insurance.delete()
        return Response({"message": "보험 정보가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)