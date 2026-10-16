"""지급 결정 요청은 의도 모델보다 먼저 차단한다. 일반 약관 비율·기한 질의는 허용한다."""

import re


def refusal_reason(message):
    message = re.sub(r"\s+", "", message)
    if re.search(r"주민\s*등록|주민번호|계좌번호|연락처.*전체", message):
        return "privacy"
    if re.search(r"보험사기|사기\s*같|사기.*판단", message):
        return "fraud"
    if re.search(
        r"지급해도|지급해줘|(?:이거|고객).*(?:지급가능|지급승인)|지급\s*(?:여부|승인).*결정|(?:지급액|지급금액).*계산|얼마.*(?:지급|받)|지급.*얼마",
        message,
    ):
        return "payment"
    if re.search(r"자동차.*과실", message):
        return "scope"
    return None
