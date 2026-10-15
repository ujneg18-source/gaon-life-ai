"""김유정(가상) 시연 서류 세트 생성기.

- 값은 아래 DATA 한 곳에서 정의 → HTML 서식 · 정답 JSON이 같은 값을 쓴다 (정답 불일치 방지)
- 의도적으로 심은 문제:
    CV-01 진단일(09.18) < 병리 보고일(09.21)
    CV-02 입퇴원확인서 9일 vs 세부내역서 8일
    CV-04 세부내역서에 수술 행위 있음 → 수술확인서는 만들지 않음(누락)
    저신뢰 유도: 진단서 질병분류기호 위에 직인
    약관 대조: 약제비 영수증의 종합비타민정(처방전에 없음, 일반의약품)
- 모든 기관 · 인물 · 주소 · 번호는 가상. 각 서류에 "SAMPLE · 가상 데이터" 표시.

사용: python gen_kim_yujeong.py <출력폴더>
"""
import json, pathlib, sys

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "kim_yujeong")
(OUT / "html").mkdir(parents=True, exist_ok=True)
(OUT / "answers").mkdir(parents=True, exist_ok=True)

HOSP = {"name": "하람대학교병원", "en": "HARAM UNIVERSITY HOSPITAL (SAMPLE)",
        "addr": "가상시 표본구 예시로 100", "tel": "000-0000-0000"}
PHARM = {"name": "새솔약국", "addr": "가상시 표본구 예시로 102", "tel": "000-0000-0001"}
PATIENT = {"name": "김유정", "sex": "여", "birth": "1988.05.20", "reg_no": "20-4471185"}
DOCTOR = {"name": "정민호", "dept": "외과", "license": "제00000호"}
PATHOLOGIST = "윤서아"

# ---------------- 세부내역서 항목 (영수증은 여기서 합산) ----------------
COPAY = 0.05  # 암 산정특례 본인부담 5% (급여 항목)
ITEMS = [
    # date, category, code(가상), name, unit, qty, days, covered
    ("2026-09-22", "입원료", "AA-0101", "입원료(일반병실)", 85000, 1, 8, True),
    ("2026-09-22", "검사료", "BB-2201", "일반혈액검사", 45000, 1, 2, True),
    ("2026-09-22", "영상진단료", "CC-3105", "복부 CT(조영제)", 220000, 1, 1, True),
    ("2026-09-23", "마취료", "DD-4010", "전신마취", 450000, 1, 1, True),
    ("2026-09-23", "처치 및 수술료", "SS-7702", "복강경하 결장 부분절제술", 3200000, 1, 1, True),
    ("2026-09-23", "치료재료대", "MM-5520", "복강경 수술 재료", 640000, 1, 1, True),
    ("2026-09-22", "주사료", "EE-6012", "수액 · 항생제 주사", 32000, 1, 8, True),
    ("2026-09-22", "투약 및 조제료", "FF-1003", "원내 투약", 12000, 1, 8, True),
    ("2026-09-22", "상급병실료 차액", "NN-9001", "2인실 차액", 70000, 1, 8, False),
]
def won(n): return f"{n:,}"
rows = []
for d, cat, code, name, unit, qty, days, cov in ITEMS:
    total = unit * qty * days
    copay = round(total * COPAY) if cov else 0
    rows.append(dict(date=d, category=cat, code=code, name=name, unit=unit, qty=qty, days=days,
                     total=total, covered=cov, copay=copay, nhis=(total - copay) if cov else 0,
                     non_covered=0 if cov else total))
cov_total = sum(r["total"] for r in rows if r["covered"])
copay_total = sum(r["copay"] for r in rows)
nhis_total = sum(r["nhis"] for r in rows)
noncov_total = sum(r["non_covered"] for r in rows)
patient_total = copay_total + noncov_total

DRUGS_RX = [  # 처방전 (퇴원약)
    ("카페시타빈정 500mg", "1정", 2, 14),
    ("온단세트론정 8mg", "1정", 2, 14),
]
PHARM_ITEMS = [  # 약제비 영수증
    ("카페시타빈정 500mg", 14, 210000, True),
    ("온단세트론정 8mg", 14, 56000, True),
    ("조제료", 14, 18000, True),
    ("종합비타민정 (일반의약품)", 30, 15000, False),  # 처방전에 없음 → 약관 대조 대상
]
ph_cov = sum(a for _, _, a, c in PHARM_ITEMS if c)
ph_copay = round(ph_cov * COPAY)
ph_non = sum(a for _, _, a, c in PHARM_ITEMS if not c)

# ---------------- 공통 HTML ----------------
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fff;font-family:"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#1f2a44}
.page{width:1240px;height:1754px;padding:90px 96px;position:relative;background:#fff}
.sample{position:absolute;top:36px;right:44px;border:3px solid #c0392b;color:#c0392b;font-weight:700;font-size:22px;padding:6px 14px;letter-spacing:.06em;transform:rotate(3deg)}
.hosp{text-align:center;color:#1f3c88}
.hosp .n{font-size:46px;font-weight:700;letter-spacing:.12em}
.hosp .e{font-size:17px;letter-spacing:.18em;margin-top:4px}
h1{text-align:center;font-size:44px;letter-spacing:.5em;margin:34px 0 26px;color:#1f3c88}
table{width:100%;border-collapse:collapse;font-size:23px}
td,th{border:2px solid #2b4a9a;padding:12px 14px;vertical-align:middle}
th{background:#eef2fb;font-weight:500;color:#1f3c88;white-space:nowrap}
.r{text-align:right;font-variant-numeric:tabular-nums}
.c{text-align:center}
.big{font-size:27px;font-weight:700}
.note{font-size:21px;line-height:1.7;margin-top:22px}
.foot{position:absolute;left:96px;right:96px;bottom:90px;font-size:22px;line-height:1.7}
.seal{display:inline-block;width:96px;height:96px;border:4px solid rgba(200,30,40,.75);color:rgba(200,30,40,.8);border-radius:8px;text-align:center;font-weight:700;font-size:20px;line-height:1.25;padding-top:14px;vertical-align:middle;margin-left:16px;transform:rotate(-6deg)}
.stamp-round{position:absolute;width:150px;height:150px;border:5px solid rgba(200,30,40,.55);border-radius:50%;color:rgba(200,30,40,.6);font-weight:700;font-size:24px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.2;transform:rotate(-14deg);pointer-events:none}
.small{font-size:19px;color:#4a5878}
"""
def page(title, body, kind="hosp"):
    head = (f'<div class="hosp"><div class="n">{HOSP["name"]}</div><div class="e">{HOSP["en"]}</div></div>'
            if kind == "hosp" else
            f'<div class="hosp"><div class="n">{PHARM["name"]}</div><div class="e">PHARMACY (SAMPLE)</div></div>')
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title>
<style>{CSS}</style></head><body><div class="page"><div class="sample">SAMPLE · 가상 데이터</div>
{head}<h1>{title}</h1>{body}</div></body></html>"""

def hosp_foot(date):
    return (f'<div class="foot">발행일 {date}<br>{HOSP["name"]} · {HOSP["addr"]} · TEL {HOSP["tel"]}'
            f'<span class="seal">하람<br>대학교<br>병원인</span></div>')

docs, answers = {}, {}

# 1) 진단서 ------------------------------------------------------------
docs["01_diagnosis"] = page("진 단 서", f"""
<table>
<tr><th>등록번호</th><td>{PATIENT['reg_no']}</td><th>환자 성명</th><td>{PATIENT['name']}</td></tr>
<tr><th>성별</th><td>{PATIENT['sex']}</td><th>생년월일</th><td>{PATIENT['birth']}</td></tr>
<tr><th>주소</th><td colspan="3">가상시 표본구 예시로 7</td></tr>
</table>
<table style="margin-top:22px">
<tr><th style="width:24%">병명</th><td colspan="3" class="big">구불결장의 악성 신생물</td></tr>
<tr><th>질병분류기호</th><td style="position:relative;height:96px" colspan="3"><span class="big" style="font-family:monospace;font-size:32px">C18.7</span>
  <span class="stamp-round" style="left:40px;top:-30px">하람대<br>병원장</span></td></tr>
<tr><th>발병일</th><td>2026.09.10</td><th>진단일</th><td class="big">2026.09.18</td></tr>
<tr><th>치료 내용 및<br>향후 치료 의견</th><td colspan="3" style="height:210px;vertical-align:top;line-height:1.7">대장내시경 생검 결과 선암 확인.<br>복강경하 결장 부분절제술 시행 예정이며, 수술 후 보조 항암치료가 필요함.</td></tr>
<tr><th>용도</th><td colspan="3">보험회사 제출용</td></tr>
</table>
<p class="note">위와 같이 진단합니다.</p>
<table style="width:70%;margin-left:auto;margin-top:10px">
<tr><th>진료과</th><td>{DOCTOR['dept']}</td><th>면허번호</th><td>{DOCTOR['license']}</td></tr>
<tr><th>의사 성명</th><td colspan="3">{DOCTOR['name']} (서명)</td></tr>
</table>
{hosp_foot('2026.10.02')}""")
answers["01_diagnosis"] = {"doc_type": "diagnosis", "patient_name": PATIENT["name"], "issuer": HOSP["name"],
    "issued_date": "2026-10-02", "diagnosis_code": "C18.7", "diagnosis_name": "구불결장의 악성 신생물",
    "diagnosis_date": "2026-09-18", "onset_date": "2026-09-10",
    "_planted": ["CV-01 진단일이 병리 보고일(2026-09-21)보다 빠름", "질병분류기호 위 직인 겹침(저신뢰 유도)"]}

# 2) 병리조직검사 결과지 -------------------------------------------------
docs["02_pathology"] = page("병리조직검사 결과지", f"""
<table>
<tr><th>등록번호</th><td>{PATIENT['reg_no']}</td><th>환자 성명</th><td>{PATIENT['name']}</td></tr>
<tr><th>성별 / 생년월일</th><td>{PATIENT['sex']} / {PATIENT['birth']}</td><th>의뢰과</th><td>{DOCTOR['dept']}</td></tr>
<tr><th>검체 접수일</th><td>2026.09.16</td><th>보고일</th><td class="big">2026.09.21</td></tr>
<tr><th>병리번호</th><td>S26-018342</td><th>의뢰의</th><td>{DOCTOR['name']}</td></tr>
</table>
<table style="margin-top:22px">
<tr><th style="width:24%">검체</th><td>대장 조직 (구불결장), 내시경 생검</td></tr>
<tr><th>육안 소견</th><td style="height:150px;vertical-align:top;line-height:1.7">회백색 조직 절편 4개, 최대 0.4cm.</td></tr>
<tr><th>병리 진단</th><td class="big" style="height:150px">Adenocarcinoma, moderately differentiated<br><span style="font-size:23px;font-weight:400">(중등도 분화 선암)</span></td></tr>
<tr><th>비고</th><td>악성 종양 확인. 임상 소견과 함께 판단 바람.</td></tr>
</table>
<p class="note">판독의: 병리과 {PATHOLOGIST} (서명)</p>
{hosp_foot('2026.09.21')}""")
answers["02_pathology"] = {"doc_type": "pathology", "patient_name": PATIENT["name"], "issuer": HOSP["name"],
    "specimen": "대장 조직 (구불결장), 내시경 생검", "pathology_result": "Adenocarcinoma, moderately differentiated",
    "report_date": "2026-09-21"}

# 3) 입퇴원확인서 ---------------------------------------------------------
docs["03_admission"] = page("입 퇴 원 확 인 서", f"""
<table>
<tr><th>등록번호</th><td>{PATIENT['reg_no']}</td><th>환자 성명</th><td>{PATIENT['name']}</td></tr>
<tr><th>성별</th><td>{PATIENT['sex']}</td><th>생년월일</th><td>{PATIENT['birth']}</td></tr>
</table>
<table style="margin-top:22px">
<tr><th style="width:24%">진료과</th><td>{DOCTOR['dept']}</td><th>병명 코드</th><td style="font-family:monospace">C18.7</td></tr>
<tr><th>병명</th><td colspan="3">구불결장의 악성 신생물</td></tr>
<tr><th>입원일</th><td class="big">2026.09.22</td><th>퇴원일</th><td class="big">2026.09.30</td></tr>
<tr><th>입원 일수</th><td colspan="3" class="big">9일</td></tr>
<tr><th>입원 사유</th><td colspan="3">복강경하 결장 부분절제술</td></tr>
<tr><th>용도</th><td colspan="3">보험회사 제출용</td></tr>
</table>
<p class="note">위 환자는 상기 기간 동안 본원에 입원하였음을 확인합니다.</p>
{hosp_foot('2026.10.02')}""")
answers["03_admission"] = {"doc_type": "admission", "patient_name": PATIENT["name"], "issuer": HOSP["name"],
    "admit_date": "2026-09-22", "discharge_date": "2026-09-30", "stay_days": 9, "diagnosis_code": "C18.7",
    "_planted": ["CV-02 입원 일수 9일 vs 세부내역서 8일"]}

# 4) 진료비 계산서 · 영수증 (입원) -----------------------------------------
cats = {}
for r in rows:
    c = cats.setdefault(r["category"], {"copay": 0, "nhis": 0, "non": 0})
    c["copay"] += r["copay"]; c["nhis"] += r["nhis"]; c["non"] += r["non_covered"]
cat_rows = "".join(
    f'<tr><td>{k}</td><td class="r">{won(v["copay"]) if v["copay"] else "-"}</td><td class="r">{won(v["nhis"]) if v["nhis"] else "-"}</td>'
    f'<td class="r">{won(v["non"]) if v["non"] else "-"}</td><td class="r">{won(v["copay"]+v["nhis"]+v["non"])}</td></tr>'
    for k, v in cats.items())
docs["04_medical_receipt"] = page("진료비 계산서 · 영수증", f"""
<table style="font-size:21px">
<tr><th>환자등록번호</th><td>{PATIENT['reg_no']}</td><th>환자 성명</th><td>{PATIENT['name']}</td></tr>
<tr><th>진료기간</th><td>2026.09.22 ~ 2026.09.29</td><th>입원 일수</th><td>8일</td></tr>
<tr><th>진료과</th><td>{DOCTOR['dept']}</td><th>환자구분</th><td>건강보험 · 산정특례(암)</td></tr>
</table>
<table style="margin-top:18px;font-size:21px">
<tr><th rowspan="2">항목</th><th colspan="2">급여</th><th rowspan="2">비급여</th><th rowspan="2">합계</th></tr>
<tr><th>본인부담금</th><th>공단부담금</th></tr>
{cat_rows}
<tr><th>합계</th><td class="r big">{won(copay_total)}</td><td class="r big">{won(nhis_total)}</td><td class="r big">{won(noncov_total)}</td><td class="r big">{won(cov_total+noncov_total)}</td></tr>
</table>
<table style="margin-top:18px;width:60%;margin-left:auto">
<tr><th>환자부담 총액</th><td class="r big">{won(patient_total)}</td></tr>
<tr><th>이미 납부한 금액</th><td class="r">0</td></tr>
<tr><th>납부할 금액</th><td class="r big">{won(patient_total)}</td></tr>
</table>
{hosp_foot('2026.09.30')}""")
answers["04_medical_receipt"] = {"doc_type": "medical_receipt", "source": "silson24", "patient_name": PATIENT["name"],
    "issuer": HOSP["name"], "period_start": "2026-09-22", "period_end": "2026-09-29", "inpatient_days": 8,
    "covered_copay": copay_total, "covered_nhis": nhis_total, "non_covered": noncov_total, "total": cov_total + noncov_total,
    "patient_total": patient_total}

# 5) 진료비 세부내역서 ----------------------------------------------------
item_rows = "".join(
    f'<tr><td class="c">{r["date"][5:].replace("-",".")}</td><td>{r["category"]}</td><td style="font-family:monospace">{r["code"]}</td>'
    f'<td>{r["name"]}</td><td class="r">{won(r["unit"])}</td><td class="c">{r["qty"]}</td><td class="c">{r["days"]}</td>'
    f'<td class="r">{won(r["total"])}</td><td class="c">{"급여" if r["covered"] else "비급여"}</td></tr>' for r in rows)
docs["05_medical_detail"] = page("진료비 세부산정내역", f"""
<table style="font-size:20px">
<tr><th>환자 성명</th><td>{PATIENT['name']}</td><th>진료기간</th><td>2026.09.22 ~ 2026.09.29</td><th>입원 일수</th><td>8일</td></tr>
</table>
<table style="margin-top:18px;font-size:18px">
<tr><th>일자</th><th>항목</th><th>코드</th><th>명칭</th><th>단가</th><th>횟수</th><th>일수</th><th>금액</th><th>구분</th></tr>
{item_rows}
<tr><th colspan="7">합계</th><td class="r big">{won(cov_total+noncov_total)}</td><td></td></tr>
</table>
<p class="note small">※ 코드는 가상 코드입니다. 실손24 전송 데이터를 서식으로 표시한 것입니다.</p>
{hosp_foot('2026.09.30')}""")
answers["05_medical_detail"] = {"doc_type": "medical_detail", "source": "silson24", "patient_name": PATIENT["name"],
    "period_start": "2026-09-22", "period_end": "2026-09-29", "inpatient_days": 8,
    "items": [{"date": r["date"], "category": r["category"], "code": r["code"], "name": r["name"],
               "covered": r["covered"], "amount": r["total"]} for r in rows],
    "_planted": ["CV-04 '처치 및 수술료' 항목 있음 → 수술확인서 필요(미제출)", "CV-02 입원 8일"]}

# 6) 처방전 ---------------------------------------------------------------
rx_rows = "".join(f'<tr><td>{n}</td><td class="c">{d}</td><td class="c">{t}</td><td class="c">{days}</td></tr>' for n, d, t, days in DRUGS_RX)
docs["06_prescription"] = page("처 방 전", f"""
<table>
<tr><th>교부번호</th><td>2026-0930-01452</td><th>교부일</th><td>2026.09.30</td></tr>
<tr><th>환자 성명</th><td>{PATIENT['name']}</td><th>생년월일</th><td>{PATIENT['birth']}</td></tr>
<tr><th>질병분류기호</th><td style="font-family:monospace">C18.7</td><th>처방의</th><td>{DOCTOR['name']} ({DOCTOR['license']})</td></tr>
</table>
<table style="margin-top:22px">
<tr><th>처방 의약품 명칭</th><th>1회 투약량</th><th>1일 투여 횟수</th><th>총 투약일수</th></tr>
{rx_rows}
<tr><td style="height:300px"></td><td></td><td></td><td></td></tr>
</table>
<p class="note">사용 기간: 교부일로부터 3일 이내</p>
{hosp_foot('2026.09.30')}""")
answers["06_prescription"] = {"doc_type": "prescription", "source": "silson24", "patient_name": PATIENT["name"],
    "issued_date": "2026-09-30", "diagnosis_code": "C18.7",
    "items": [{"drug_name": n, "per_day": t, "days": d} for n, _, t, d in DRUGS_RX]}

# 7) 약제비 영수증 --------------------------------------------------------
ph_rows = "".join(f'<tr><td>{n}</td><td class="c">{d}</td><td class="r">{won(a)}</td><td class="c">{"급여" if c else "비급여"}</td></tr>' for n, d, a, c in PHARM_ITEMS)
docs["07_pharmacy_receipt"] = page("약제비 계산서 · 영수증", f"""
<table>
<tr><th>환자 성명</th><td>{PATIENT['name']}</td><th>조제일</th><td>2026.09.30</td></tr>
<tr><th>처방전 교부번호</th><td>2026-0930-01452</td><th>처방 기관</th><td>{HOSP['name']}</td></tr>
</table>
<table style="margin-top:22px">
<tr><th>품명</th><th>일수</th><th>금액</th><th>구분</th></tr>
{ph_rows}
</table>
<table style="margin-top:22px;width:60%;margin-left:auto">
<tr><th>급여 본인부담금</th><td class="r">{won(ph_copay)}</td></tr>
<tr><th>비급여</th><td class="r">{won(ph_non)}</td></tr>
<tr><th>합계</th><td class="r big">{won(ph_copay+ph_non)}</td></tr>
</table>
<div class="foot">조제일 2026.09.30<br>{PHARM['name']} · {PHARM['addr']} · TEL {PHARM['tel']}<span class="seal">새솔<br>약국<br>인</span></div>""", kind="pharm")
answers["07_pharmacy_receipt"] = {"doc_type": "pharmacy_receipt", "patient_name": PATIENT["name"], "issuer": PHARM["name"],
    "issued_date": "2026-09-30",
    "items": [{"drug_name": n, "days": d, "amount": a, "covered": c} for n, d, a, c in PHARM_ITEMS],
    "covered_copay": ph_copay, "non_covered": ph_non,
    "_planted": ["약관 대조: '종합비타민정 (일반의약품)'은 처방전에 없음 · 영양제 → 보상 제외 가능성"]}

for k, html in docs.items():
    (OUT / "html" / f"{k}.html").write_text(html, encoding="utf-8")
for k, a in answers.items():
    (OUT / "answers" / f"{k}.json").write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")

claim = {"claim_id": "GA-2610-0482", "customer_name": PATIENT["name"], "policy_no": "L-2023-118203",
         "claim_types": ["cancer_diagnosis", "hospitalization", "medical_expense"],
         "submitted": {"app": ["01_diagnosis", "02_pathology", "03_admission", "07_pharmacy_receipt"],
                       "silson24": ["04_medical_receipt", "05_medical_detail", "06_prescription"]},
         "required": 8, "submitted_count": 7,
         "expected_issues": [
             {"kind": "missing", "rule": "CV-04", "title": "수술확인서 미제출"},
             {"kind": "mismatch", "rule": "CV-01", "title": "진단일이 병리 보고일보다 빠름"},
             {"kind": "mismatch", "rule": "CV-02", "title": "입원 일수 9일 vs 8일"},
             {"kind": "low_conf", "rule": "-", "title": "질병분류기호 직인 겹침 (모델 결과에 따라 발생 여부 달라짐)"},
             {"kind": "excluded_item", "rule": "coverage", "title": "종합비타민정 보상 제외 가능성"}],
         "totals": {"hospital_patient_total": patient_total, "pharmacy_patient_total": ph_copay + ph_non}}
(OUT / "answers" / "_claim.json").write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok", len(docs), "docs; hospital patient total", won(patient_total))
