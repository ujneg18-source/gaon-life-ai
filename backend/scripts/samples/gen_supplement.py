"""김유정의 원본 7장과 분리해 보완 회신용 수술확인서만 만든다."""
import json
from app.config import get_settings
from scripts.samples.common import surgery_html


def main():
    folder=get_settings().SAMPLE_PATH/'supplement'
    folder.mkdir(parents=True,exist_ok=True)
    values={'doc_type':'surgery_cert','patient_name':'김유정','issuer':'하람대학교병원',
            'issued_date':'2026-10-16','surgery_name':'복강경하 결장 부분절제술',
            'surgery_date':'2026-09-23','surgery_code':'SS-7702'}
    (folder/'수술확인서.json').write_text(json.dumps(values,ensure_ascii=False,indent=2))
    (folder/'수술확인서.html').write_text(surgery_html(values,'1988.05.20'))
    (folder/'README.md').write_text('# 보완 회신용 수술확인서 (가상)\n\n수술확인서.html/png/json은 보완 회신용입니다. 최초 7장·answers/_claim.json 제출 목록에 포함하지 않습니다. JSON은 이 파일의 정답입니다.\n')

if __name__=='__main__': main()
