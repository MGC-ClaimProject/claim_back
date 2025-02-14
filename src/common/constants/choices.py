from decimal import Decimal

STATUS_CHOICES = [
    ("Pending", "보류중"),
    ("In Progress", "진행중"),
    ("Completed", "완료"),
]

GENDER_CHOICES = [("Male", "남성"), ("Female", "여성")]


RELATION_CHOICES = [
    ("Self", "본인"),
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

# common/constants/choices.py
from common.constants.choices import INSURANCE_TYPE_CHOICES, POLICY_STATUS_CHOICES

# ✅ 보험사 선택 옵션 (카테고리별)
INSURANCE_COMPANY_CHOICES = [
    ("생명보험", (
        ("Samsung Life", "삼성생명"),
        ("Kyobo Life", "교보생명"),
        ("Hanwha Life", "한화생명"),
        ("Shinhan Life", "신한라이프"),
        ("DB Life", "DB생명"),
        ("KDB Life", "KDB생명"),
        ("NH Life", "농협생명"),
        ("DGB Life", "DGB생명"),
        ("AIA Life", "AIA생명"),
        ("MetLife", "메트라이프생명"),
        ("Prudential Life", "푸르덴셜생명"),
        ("Heungkuk Life", "흥국생명"),
        ("Chubb Life", "처브라이프생명"),
        ("ABL Life", "ABL생명"),
        ("Tongyang Life", "동양생명"),
        ("Mirae Asset Life", "미래에셋생명"),
        ("IBK Pension", "IBK연금보험"),
    )),
    ("손해보험", (
        ("Samsung Fire & Marine", "삼성화재"),
        ("Hyundai Marine & Fire", "현대해상"),
        ("DB Insurance", "DB손해보험"),
        ("KB Insurance", "KB손해보험"),
        ("Meritz Fire & Marine", "메리츠화재"),
        ("Heungkuk Fire & Marine", "흥국화재"),
        ("MG Non-Life", "MG손해보험"),
        ("Hanwha General Insurance", "한화손해보험"),
        ("NH Non-Life", "농협손해보험"),
        ("AXA Direct", "악사손해보험"),
        ("Lotte Insurance", "롯데손해보험"),
        ("Carrot General Insurance", "캐롯손해보험"),
        ("AIG General Insurance", "AIG손해보험"),
        ("Chubb General Insurance", "처브손해보험"),
    )),
    ("기타보험", (
        ("Korean Federation of Community Credit", "신협공제"),
        ("National Credit Union Federation", "새마을금고공제"),
        ("Korea Teachers' Credit Union", "교직원공제회"),
        ("Post Insurance", "우체국보험"),
    )),
]

