from decimal import Decimal

STATUS_CHOICES = [
    ("Pending", "보류중"),
    ("In Progress", "진행중"),
    ("Completed", "완료"),
]

GENDER_CHOICES = [("Male", "남성"), ("Female", "여성")]


RELATION_CHOICES = [
    ("Parant", "부모"),
    ("Spouse", "배우자"),
    ("Child", "자녀"),
    ("Relative", "친척"),
    ("Grandparent", "조부모"),
    ("ETC", "기타"),
]

INSURANCE_TYPE_CHOICES = [
    ("LIFE", "종신보험"),
    ("INDEMNITY", "실손보험"),
    ("HEALTH", "건강종합보험"),
]

POLICY_STATUS_CHOICES = [
    ("active", "유지 중"),
    ("expired", "만료"),
    ("cancelled", "해지"),
    ("pending", "대기 중"),
]

CLAIM_STATUS_CHOICES = [
    ("draft", "작성중"),  # 사용자가 작성 중인 상태
    ("completed", "작성완료"),  # 작성 완료 상태
    ("sending", "발송중"),  # 발송 중 상태
    ("send_error", "발송에러"),  # 발송 에러 상태
    ("sent", "발송완료"),  # 발송 완료 상태
    ("claimed", "청구 완료"),  # 보험 청구가 완료된 상태
    ("cancelled", "청구 취소"),  # 보험 청구가 취소된 상태
    ("received", "수령 완료"),  # 보험금이 수령된 상태
]
