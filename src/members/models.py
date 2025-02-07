from common.constants.choices import GENDER_CHOICES, RELATION_CHOICES
from django.db import models
from users.models import User


class Member(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # 유저 삭제 시 멤버도 삭제됨
        related_name="members",  # ✅ `user.members.all()`로 접근 가능
        null=True,  # ✅ 기존 데이터와 호환성 유지 (기존 멤버에는 user가 없을 수 있음)
        blank=True,
    )
    name = models.CharField(max_length=30, verbose_name="이름")
    phone = models.CharField(max_length=30, verbose_name="전화번호")
    birth = models.DateField(verbose_name="생년월일")
    gender = models.CharField(
        max_length=30, choices=GENDER_CHOICES, verbose_name="성별"
    )
    relation = models.CharField(
        max_length=30, choices=RELATION_CHOICES, verbose_name="관계"
    )
    is_ad_agreed = models.BooleanField(default=False, verbose_name="광고성 정보 동의")  # ✅ 선택 동의 필드 추가
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "가족 멤버"
        verbose_name_plural = "가족 멤버들"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "phone", "birth"], name="unique_member"
            )
        ]  # 중복 방지

    def __str__(self):
        return f"{self.name} ({self.relation})"

    @property
    def age(self):
        """현재 날짜를 기준으로 나이를 계산"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.birth.year
            - ((today.month, today.day) < (self.birth.month, self.birth.day))
        )


class Security(models.Model):
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name="security",
        verbose_name="멤버 보안",
    )
    sign = models.CharField(max_length=255, verbose_name="서명")  # 서명 필드
    account = models.CharField(max_length=30, verbose_name="계좌 번호")
    bank = models.CharField(max_length=30, verbose_name="은행 이름")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "보안 정보"
        verbose_name_plural = "보안 정보들"

    def __str__(self):
        return f"{self.member.name}의 보안 정보"
