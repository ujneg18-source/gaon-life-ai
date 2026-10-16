"""공통 가상 서류 생성: python -m scripts.samples.gen_claim --customer DEMO-C002.

HTML·정답은 같은 프로필을 쓴다. PNG는 브라우저로 HTML을 1240×1754 캡처한다.
김유정 최초7장·해시는 보존하고 다른 고객 서류만 렌더링한다.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import json
from html import escape

from app.config import get_settings
from scripts.samples.common import page, surgery_html

LABELS = {
    "patient_name": "환자 성명",
    "issuer": "발행 기관",
    "issued_date": "발행일",
    "diagnosis_code": "질병분류기호",
    "diagnosis_name": "진단명",
    "diagnosis_date": "진단일",
    "pathology_result": "병리 진단",
    "specimen": "검체",
    "report_date": "병리 보고일",
    "admit_date": "입원일",
    "discharge_date": "퇴원일",
    "stay_days": "입원 일수",
    "period_start": "진료 시작일",
    "period_end": "진료 종료일",
    "inpatient_days": "입원료 산정 일수",
    "covered_copay": "급여 본인부담금",
    "non_covered": "비급여",
    "patient_total": "환자 부담 합계",
    "total": "진료비 합계",
}
TITLES = {
    "diagnosis": "진 단 서",
    "pathology": "조직검사 결과지",
    "admission": "입퇴원확인서",
    "medical_receipt": "진료비 계산서 · 영수증",
    "medical_detail": "진료비 세부산정내역",
    "prescription": "처 방 전",
    "pharmacy_receipt": "약제비 계산서 · 영수증",
}


def render(values, birth):
    """기관·고객은 프로필에서 받으며 표의 금액과 정답을 따로 계산하지 않는다."""
    if values["doc_type"] == "surgery_cert":
        return surgery_html(values, birth)
    body = (
        "<table>"
        + "".join(
            f"<tr><th>{LABELS.get(k, k)}</th><td>{escape(str(v)) if v != '' else '(미기재)'}</td></tr>"
            for k, v in values.items()
            if k not in ("doc_type", "items")
        )
        + "</table>"
    )
    items = values.get("items", [])
    if items:
        drug = values["doc_type"] in ("prescription", "pharmacy_receipt")
        columns = (
            [("drug_name", "품명"), ("days", "일수"), ("amount", "금액"), ("covered", "구분")]
            if drug
            else [
                ("name", "항목명"),
                ("code", "코드"),
                ("category", "분류"),
                ("amount", "금액"),
                ("covered", "구분"),
            ]
        )
        body += (
            '<table style="margin-top:24px"><tr>'
            + "".join(f"<th>{label}</th>" for _, label in columns)
            + "</tr>"
        )
        for item in items:
            body += (
                "<tr>"
                + "".join(
                    "<td>"
                    + escape(
                        "급여"
                        if item.get(k) is True
                        else "비급여"
                        if item.get(k) is False
                        else str(item.get(k, ""))
                    )
                    + "</td>"
                    for k, _ in columns
                )
                + "</tr>"
            )
        body += "</table>"
    body += '<div class="foot">가상 서류 · 실제 의료정보가 아닙니다.<br>담당 의사 정민호 (가상 · 제00000호)</div>'
    return page(TITLES[values["doc_type"]], body, values["issuer"])


def generate(customer_id, config=None, use_photo=False):
    config = config or get_settings()
    manifest = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    customers = [
        c
        for c in manifest["customers"]
        if customer_id in (c["id"], c["sample_id"]) or customer_id == "all"
    ]
    if not customers:
        raise ValueError("고객 ID가 없습니다")
    outputs = []
    for c in customers:
        folder = config.SAMPLES_ROOT / c["sample_id"]
        for sub in ("html", "png", "answers", "photo"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        for doc in c["documents"]:
            stem = doc["stem"]
            values = doc["values"]
            if c["sample_id"] != "kim_yujeong":
                (folder / "html" / f"{stem}.html").write_text(render(values, c["birth_date"]))
                (folder / "answers" / f"{stem}.json").write_text(
                    json.dumps(values, ensure_ascii=False, indent=2)
                )
            if use_photo and doc["source"] == "image":
                from scripts.samples.verify_samples import image_path

                image_path(
                    folder, stem, config, True
                )  # 중복 사진만 거절하고 없는 장은 깨끗한 PNG를 쓴다.
        if use_photo:
            from scripts.samples.verify_samples import image_path

            selected = {
                d["stem"]: str(image_path(folder, d["stem"], config, True))
                for d in c["documents"]
                if d["source"] == "image"
            }
            (folder / "selected_inputs.json").write_text(
                json.dumps(selected, ensure_ascii=False, indent=2)
            )
        expected = {"claim_id": c["primary_claim_id"], "expected_issues": c["expected_issues"]}
        if c["sample_id"] != "kim_yujeong":
            (folder / "answers" / "_claim.json").write_text(
                json.dumps(expected, ensure_ascii=False, indent=2)
            )
            notes = (
                "\n".join(f"- {i['rule']}: {i['kind']}" for i in c["expected_issues"])
                or "- 없음(서류 미제출은 처리 전)"
            )
            (folder / "README.md").write_text(
                f"# {c['name']} (가상) · {c['scenario']}\n\n고객: {c['id']}, 청구: {c['primary_claim_id']}\n\n## 심어 둔 이슈\n{notes}\n\n## 파일\nhtml/ 원본 · png/ 1240×1754 캡처 · answers/ 정답. 실제 호출 여부는 DB provenance로 확인하며 프로필의 live는 검증 허용 목록입니다.\n\n## 사진\nphoto/에 PNG와 같은 stem으로 .jpg/.png/.jpeg 한 장만 저장합니다. --use-photo는 image 원본만 사진으로 바꾸며 실손24는 JSON을 유지합니다.\n"
            )
        (folder / "photo" / "README.md").write_text(
            "PNG와 같은 파일명(stem)의 .jpg/.png/.jpeg를 한 장만 저장합니다. 사진의 글자·숫자는 원본과 같아야 합니다.\n"
        )
        if c["id"] == "DEMO-C005":
            readme = folder / "README.md"
            readme.write_text(
                readme.read_text()
                + "\n실손 통원이며 통원일당 특약 청구가 아닙니다. 진료·약제비 통합 내역을 전자 3종으로 받는 데모 경로입니다.\n"
            )
        outputs.append(str(folder))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customer", required=True)
    parser.add_argument("--use-photo", action="store_true")
    parser.add_argument(
        "--html-only", action="store_true", help="HTML/정답만 작성하고 PNG 캡처는 분리 실행"
    )
    args = parser.parse_args()
    folders = generate(args.customer, use_photo=args.use_photo)
    if not args.html_only:
        from scripts.samples.render import render_folder

        for folder in folders:
            render_folder(Path(folder))
    print("\n".join(folders))


if __name__ == "__main__":
    main()
