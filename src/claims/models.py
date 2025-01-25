from common.constants.choices import CLAIM_STATUS_CHOICES
from django.db import models
from members.models import Member


class Claim(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="claims", verbose_name="피보험자"
    )
    incident_date = models.DateField(verbose_name="사고 발생일")
    symptoms = models.TextField(verbose_name="증상")
    claim_insurers = models.JSONField(
        verbose_name="청구 보험사 리스트",
        default=list,
        help_text="청구 대상 보험사 리스트를 JSON 형식으로 저장합니다.",
    )  # JSON 필드로 여러 보험사 저장
    is_required_agreement = models.BooleanField(
        default=False, verbose_name="필수 동의 여부"
    )
    bank = models.CharField(max_length=50, verbose_name="은행명", blank=True, null=True)
    account = models.CharField(
        max_length=30, verbose_name="계좌 번호", blank=True, null=True
    )
    is_same_as_payout_account = models.BooleanField(
        default=True, verbose_name="출금 계좌와 동일 여부"
    )
    claim_status = models.CharField(
        max_length=20,
        choices=CLAIM_STATUS_CHOICES,
        default="draft",
        verbose_name="청구 상태",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "보험 청구"
        verbose_name_plural = "보험 청구들"

    def __str__(self):
        return f"청구: {getattr(self.member, 'name', 'Unknown')} - {self.incident_date}"


class AddDocument(models.Model):
    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE, related_name="documents", verbose_name="청구"
    )
    document = models.FileField(upload_to="claim_documents/", verbose_name="추가 문서")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "추가 문서"
        verbose_name_plural = "추가 문서들"

    def __str__(self):
        return f"문서: {self.claim.id} - {self.document.name}"
