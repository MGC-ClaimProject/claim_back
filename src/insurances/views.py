import random
from datetime import date, timedelta

from drf_spectacular.utils import extend_schema
from insurances.models import Insurance
from insurances.serializers import InsuranceSerializer
from members.models import Member
from rest_framework import status
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView,
                                     get_object_or_404)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
        return Response(
            {"message": "보험 정보가 삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT,
        )


class UpdateMemberInsurancesView(APIView):
    """
    특정 멤버의 보험 데이터를 5~10개 랜덤 생성하여 갱신하는 API
    """

    def post(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)

        # 기존 보험 삭제
        Insurance.objects.filter(member=member).delete()

        # 새로운 랜덤 보험 생성
        insurance_list = []
        for _ in range(random.randint(5, 10)):  # 5~10개 보험 생성
            insurance = Insurance.objects.create(
                member=member,
                company=random.choice(
                    ["삼성화재", "현대해상", "DB손해보험", "KB손해보험", "한화손해보험"]
                ),
                type=random.choice(
                    [
                        "건강보험",
                        "자동차보험",
                        "여행자보험",
                        "생명보험",
                        "운전자보험",
                        "재산보험",
                    ]
                ),
                policy_name=f"{member.name}님의 {random.choice(['건강보험', '자동차보험', '생명보험'])}",
                premium=random.randint(10000, 500000),
                start_date=date.today() - timedelta(days=random.randint(30, 365 * 3)),
                end_date=date.today() + timedelta(days=random.randint(30, 365 * 5)),
                payment_term=random.randint(1, 10),
                is_renewable=random.choice([True, False]),
                status=random.choice(["active", "expired", "pending"]),
            )
            insurance_list.append(insurance)

        return Response(
            {
                "message": f"{member.name}님의 보험 정보가 갱신되었습니다.",
                "insurances": [
                    {
                        "policy_name": i.policy_name,
                        "company": i.company,
                        "premium": i.premium,
                    }
                    for i in insurance_list
                ],
            },
            status=status.HTTP_201_CREATED,
        )
