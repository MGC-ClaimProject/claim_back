from common.constants.choices import (INSURANCE_COMPANY_CHOICES,
                                      INSURANCE_TYPE_CHOICES,
                                      POLICY_STATUS_CHOICES)
from django.db import models
from members.models import Member


class Insurance(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="insurances",
        verbose_name="관리자",
    )
    company = models.CharField(
        max_length=50,
        choices=INSURANCE_COMPANY_CHOICES,  # ✅ 올바른 튜플 형태 적용
        verbose_name="보험사",
    )
    type = models.CharField(
        max_length=20, choices=INSURANCE_TYPE_CHOICES, verbose_name="보험 종류"
    )
    holder = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="계약자"
    )
    insured = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="피보험자"
    )
    policy_name = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="보험 이름"
    )
    premium = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="보험료"
    )
    start_date = models.DateField(blank=True, null=True, verbose_name="보험 시작일")
    end_date = models.DateField(blank=True, null=True, verbose_name="보험 종료일")
    payment_term = models.IntegerField(blank=True, null=True, verbose_name="납입 기간")
    is_renewable = models.BooleanField(default=False, verbose_name="갱신 여부")
    status = models.CharField(
        max_length=20,
        choices=POLICY_STATUS_CHOICES,
        default="active",
        verbose_name="유지 상태",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "보험 계약"
        verbose_name_plural = "보험 계약들"

    def __str__(self):
        return f"{self.policy_name or self.company} - {self.holder}"
