"""서류별 표준 스키마의 단일 원본. 검증 모델에서 Extract용 스키마를 생성한다."""

from datetime import date as Date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Kcd = Annotated[
    str, Field(pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$", description="질병분류기호 KCD. 예: C18.7")
]
Won = Annotated[
    int, Field(ge=0, description="금액(원), 쉼표 없는 정수. 문서에 없는 값은 추측하지 않는다.")
]
Days = Annotated[int, Field(ge=0, description="일수, 정수")]


class CommonDoc(BaseModel):
    """문서에 없는 선택 항목은 None으로 둬 임의 추출값으로 채우지 않는다."""

    model_config = ConfigDict(extra="ignore")
    patient_name: str = Field(min_length=1, description="환자 성명")
    issuer: str | None = Field(default=None, description="발행 기관 이름. 없으면 빈 문자열")
    issued_date: Date | None = Field(
        default=None, description="발행일 YYYY-MM-DD. 없으면 빈 문자열"
    )


class DiagnosisDoc(CommonDoc):
    diagnosis_code: Kcd
    diagnosis_name: str = Field(description="병명")
    diagnosis_date: Date = Field(description="진단일 YYYY-MM-DD")
    onset_date: Date | None = Field(default=None, description="발병일 YYYY-MM-DD. 없으면 빈 문자열")


class PathologyDoc(CommonDoc):
    pathology_result: str = Field(description="병리 진단 원문. 영문이면 번역하지 않는다")
    specimen: str = Field(description="검체·검체 부위 원문")
    report_date: Date = Field(description="병리 보고일 YYYY-MM-DD")


class AdmissionDoc(CommonDoc):
    admit_date: Date = Field(description="입원일 YYYY-MM-DD")
    discharge_date: Date = Field(description="퇴원일 YYYY-MM-DD")
    stay_days: Days
    diagnosis_code: Kcd | None = None


class SurgeryDoc(CommonDoc):
    surgery_name: str = Field(description="수술명")
    surgery_date: Date = Field(description="수술일 YYYY-MM-DD")
    surgery_code: str | None = None


class MedicalItem(BaseModel):
    """표의 한 행. 테이블은 객체 배열이며 배열 안에 배열을 두지 않는다."""

    name: str = Field(description="항목 이름 원문")
    code: str | None = Field(default=None, description="항목 코드")
    category: str | None = Field(
        default=None, description="분류 원문. 수술료는 surgery로 정규화 가능"
    )
    covered: bool | None = Field(default=None, description="급여면 true, 비급여면 false")
    amount: Won
    date: Date | None = None


class MedicalDoc(CommonDoc):
    period_start: Date = Field(description="진료 시작일 YYYY-MM-DD")
    period_end: Date = Field(description="진료 종료일 YYYY-MM-DD")
    inpatient_days: Days | None = None
    covered_copay: Won | None = None
    covered_nhis: Won | None = None
    non_covered: Won | None = None
    total: Won | None = None
    patient_total: Won | None = None
    items: list[MedicalItem] = Field(
        default_factory=list, description="진료비 항목 표. 없으면 빈 배열"
    )


class DrugItem(BaseModel):
    drug_name: str = Field(description="의약품·조제료 이름과 규격. 원문대로")
    per_day: Days | None = None
    days: Days | None = None
    amount: Won | None = None
    covered: bool | None = Field(default=None, description="급여면 true, 비급여면 false")


class PharmacyDoc(CommonDoc):
    items: list[DrugItem] = Field(description="약품별 이름·투약 일수·금액·급여 구분")
    diagnosis_code: Kcd | None = None
    covered_copay: Won | None = None
    non_covered: Won | None = None


class OutpatientDoc(CommonDoc):
    visit_dates: list[Date] = Field(description="통원 진료일 목록 YYYY-MM-DD")


class DisabilityDoc(CommonDoc):
    disability_part: str
    disability_rate: float = Field(ge=0, le=100, description="장해 지급률(%)")


class ImagingDoc(CommonDoc):
    findings: str = Field(description="영상 판독 소견 원문")


class DeathDoc(CommonDoc):
    death_date: Date = Field(description="사망일 YYYY-MM-DD")


class ClaimFormDoc(CommonDoc):
    claim_types: list[str]
    accident_date: Date | None = None
    bank_name: str | None = None


DOCUMENT_SCHEMAS: dict[str, type[CommonDoc]] = {
    "diagnosis": DiagnosisDoc,
    "pathology": PathologyDoc,
    "admission": AdmissionDoc,
    "surgery_cert": SurgeryDoc,
    "medical_receipt": MedicalDoc,
    "medical_detail": MedicalDoc,
    "prescription": PharmacyDoc,
    "pharmacy_receipt": PharmacyDoc,
    "outpatient": OutpatientDoc,
    "disability": DisabilityDoc,
    "imaging_report": ImagingDoc,
    "death_cert": DeathDoc,
    "claim_form": ClaimFormDoc,
}
