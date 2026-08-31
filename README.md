# 개인정보 마스킹 도구

Windows PC에서 로컬로 실행되는 개인정보 마스킹 프로그램입니다. 사용자가 문서 파일을 선택하면 개인정보 후보를 탐지하고, 사용자가 검토·수정한 항목만 마스킹된 사본으로 저장합니다. 원본 파일은 수정하거나 덮어쓰지 않습니다.

## 현재 지원 기능

- XLSX: 문자열 셀 개인정보 후보 탐지 및 선택 항목 치환 저장
- DOCX: 본문 문단과 표 셀 개인정보 후보 탐지 및 선택 항목 치환 저장
- PDF: 텍스트 PDF 개인정보 후보 탐지 및 PyMuPDF redaction 저장
- 스캔 PDF: Tesseract OCR 기반 후보 탐지와 이미지 영역 마스킹 저장
- HWPX: ZIP 내부 XML 텍스트 기반 개인정보 후보 탐지 및 선택 항목 치환 저장
- HWP: 안정 지원 대상이 아니며 HWPX 변환 안내 표시
- CSV 처리 로그: 원문 개인정보와 마스킹 문자열을 저장하지 않는 구조
- Windows exe 배포 준비: PyInstaller `onedir` 빌드 설정과 배치 파일 제공

## 제한사항

- 스캔 PDF OCR은 누락 또는 오탐 가능성이 있으므로 사용자가 반드시 검토해야 합니다.
- DOCX의 복잡한 run 서식, PDF의 복잡한 레이아웃, HWPX의 이미지/첨부/메타데이터 안 개인정보까지 완전 보장하지 않습니다.
- 구형 HWP 파일은 직접 마스킹하지 않습니다. 한글에서 HWPX로 변환한 뒤 처리하세요.
- 설치 마법사, 코드 서명, 자동 업데이트는 포함되어 있지 않습니다.
- 외부 API, 클라우드 변환 서비스, 온라인 OCR은 사용하지 않습니다.

## PDF 처리 안내

PDF는 두 종류로 나누어 처리합니다.

- 텍스트 PDF: PDF 내부에 선택 가능한 텍스트 레이어가 있는 문서입니다. PyMuPDF의 redaction 기능을 사용해 선택된 원문 영역을 제거하고, 가능한 경우 사용자가 지정한 마스킹 문구를 넣습니다. 단순히 검은 박스를 위에 덮는 방식이 아닙니다.
- 스캔 PDF: 페이지가 이미지로만 구성된 문서입니다. Tesseract OCR로 글자를 인식한 뒤, 사용자가 선택한 OCR 영역을 이미지 위에 단색 박스로 마스킹하고 새 PDF로 재구성합니다.

스캔 PDF 처리에는 로컬 Tesseract 설치가 필요합니다. OCR은 누락 또는 오탐 가능성이 있으므로 검토 화면에서 반드시 확인해야 합니다. OCR이 인식하지 못한 개인정보는 결과 파일에 남을 수 있습니다.

HWP 파일은 아직 안정 지원 대상이 아닙니다. 한글에서 HWPX로 변환한 뒤 처리하는 흐름을 권장합니다.

## HWPX / HWP 처리 안내

HWPX는 ZIP 패키지 내부 XML 텍스트를 기준으로 개인정보 후보를 탐지하고 치환합니다. 원본 HWPX 파일은 수정하지 않으며, 결과는 사용자가 선택한 저장 폴더에 `masked_원본파일명.hwpx` 형식으로 새로 저장합니다.

현재 HWPX 처리는 본문 가능성이 높은 XML 파일의 `text`와 `tail` 텍스트 노드를 중심으로 동작합니다. 내부 이미지 속 글자, 첨부 파일, 메타데이터, 매우 복잡한 레이아웃의 모든 개인정보까지 완전히 보장하지 않습니다. 일부 XML 파싱 오류가 있는 파일은 해당 XML을 건너뛰거나 저장 단계에서 실패할 수 있으므로 결과 파일을 반드시 열어 확인해야 합니다.

구형 HWP 파일은 현재 안정 지원 대상이 아닙니다. 한글에서 HWPX로 변환한 뒤 처리하세요. 개인정보 문서 보호를 위해 외부 변환 서비스나 클라우드 변환 API 사용은 권장하지 않습니다.

## 저장 정책

- 원본 파일은 수정하거나 덮어쓰지 않습니다.
- 결과 파일은 사용자가 선택한 저장 폴더에 저장합니다.
- 결과 파일명은 `masked_원본파일명` 형식을 사용합니다.
- 같은 이름이 이미 있으면 `_2`, `_3`처럼 번호를 붙입니다.
- 저장 전 원본 경로와 결과 경로가 같은지 검사합니다.
- 일부 파일 저장이 실패해도 나머지 파일 처리는 계속합니다.

## 로그 정책

- 처리 결과는 CSV 로그로 저장합니다.
- 로그 파일명은 `masking_log_YYYYMMDD_HHMMSS.csv` 형식입니다.
- CSV는 Windows Excel에서 열기 쉽도록 `utf-8-sig` 인코딩을 사용합니다.
- 로그에는 파일명, 경로, 처리 개수, 성공 여부, 실패 사유만 저장합니다.
- 로그에는 `original_text`, `masked_text`, 탐지된 개인정보 원문을 저장하지 않습니다.
- 로그 저장에 실패해도 이미 생성된 마스킹 파일은 취소하지 않고, 결과 화면에 로그 실패 사유를 표시합니다.

## 보안 정책

- 모든 처리는 로컬 PC에서 수행합니다.
- 외부 서버, 외부 API, 클라우드 저장소로 문서를 전송하지 않습니다.
- 검토 화면에는 개인정보 원문이 표시되므로 화면 공유나 캡처에 주의해야 합니다.
- 사용자가 선택한 항목만 실제 마스킹합니다.
- 스캔 PDF OCR 결과는 누락 또는 오탐 가능성이 있으므로 반드시 검토해야 합니다.
- HWP 파일은 안정 지원 대상이 아니며 HWPX 변환 후 처리를 권장합니다.

## 실패 처리

- 저장 중 일부 파일이 실패해도 앱은 중단되지 않습니다.
- 결과 화면에서 성공 파일과 실패 파일을 분리해 표시합니다.
- 실패 파일에는 실패 사유를 함께 표시합니다.
- 저장 폴더 열기 버튼으로 결과 폴더를 바로 열 수 있습니다.

## 실행 방법

```powershell
cd "C:\Users\덕유중\Documents\DATA MASKING\privacy_masker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 샘플 화면 확인

1. 앱 실행
2. `파일 추가`로 XLSX, DOCX, PDF, HWPX 샘플 파일 선택
3. 저장 폴더 선택
4. 개인정보 후보 탐지 실행
5. 검토 표에서 선택 여부와 마스킹 결과 셀을 확인 또는 수정
6. 저장 단계로 이동
7. `마스킹 사본 저장`
8. 선택한 폴더에 `masked_원본파일명` 결과 파일과 `masking_log_YYYYMMDD_HHMMSS.csv`가 생성되는지 확인

CSV 로그에는 원문 개인정보와 마스킹 결과 문자열을 저장하지 않습니다.

## 테스트

```powershell
cd "C:\Users\덕유중\Documents\DATA MASKING\privacy_masker"
pytest tests
```

테스트는 개인정보 탐지, 파일명 생성, 저장 검증, CSV 로그 보안, XLSX/DOCX/PDF/HWPX 처리, 배포 리소스 경로를 확인합니다.

---

## 현재 지원 범위와 QA 기준

현재 구현은 Windows 로컬 PC에서 문서를 외부 서버로 보내지 않고 처리하는 것을 전제로 합니다.

지원 범위:

- XLSX: 문자열 셀의 개인정보 후보 탐지 및 선택 항목 치환 저장
- DOCX: 본문 문단과 표 셀의 개인정보 후보 탐지 및 선택 항목 치환 저장
- 텍스트 PDF: PyMuPDF redaction 기반 선택 항목 제거/치환 저장
- 스캔 PDF: 로컬 Tesseract OCR 기반 후보 탐지 및 이미지 영역 마스킹 저장
- HWPX: ZIP 내부 XML 텍스트 기반 후보 탐지 및 선택 항목 치환 저장

제한 또는 미지원 범위:

- 구형 HWP는 안정 지원 대상이 아닙니다. HWPX로 변환한 뒤 처리하는 방식을 권장합니다.
- 스캔 PDF OCR은 인식 누락과 오탐 가능성이 있으므로 사용자의 검토가 반드시 필요합니다.
- DOCX의 복잡한 run 서식, PDF의 복잡한 레이아웃, HWPX의 이미지/첨부/메타데이터 안 개인정보까지 완전 보장하지 않습니다.
- 설치 마법사, 코드 서명, 자동 업데이트는 포함되어 있지 않습니다.
- 외부 API, 클라우드 변환 서비스, 온라인 OCR은 사용하지 않습니다.

## 테스트 실행

테스트용 샘플 파일을 만들려면 다음 명령을 실행합니다.

```powershell
cd "C:\Users\덕유중\Documents\DATA MASKING\privacy_masker"
python tools\create_sample_files.py
```

자동 테스트는 다음 명령으로 실행합니다.

```powershell
pytest tests
```

자세한 수동 점검표는 `README_TEST.md`를 참고하세요.

중요 QA 기준:

- 원본 파일은 저장 전후 해시가 같아야 합니다.
- 결과 파일은 사용자가 선택한 저장 폴더에 `masked_원본파일명` 형식으로 생성되어야 합니다.
- 같은 이름의 결과 파일이 있으면 `_2`, `_3` 번호가 붙어야 합니다.
- 검토 화면에서 선택한 항목만 마스킹되어야 합니다.
- 사용자가 직접 수정한 `masked_text`가 최종 결과에 반영되어야 합니다.
- CSV 로그에는 `original_text`, `masked_text`, 탐지된 개인정보 원문이 저장되면 안 됩니다.
- 파일명 자체에 개인정보가 있으면 파일명이 로그에 남을 수 있으므로, 운영 정책상 파일명에도 개인정보를 넣지 않는 것을 권장합니다.

## Windows exe 배포

Python을 모르는 사용자를 위해 PyInstaller 기반 Windows 실행 파일 배포를 준비합니다. 기본 빌드는 안정성과 문제 추적이 쉬운 `onedir` 방식입니다.

빌드 명령:

```powershell
cd "C:\Users\덕유중\Documents\DATA MASKING\privacy_masker"
build_windows.bat
```

`build_windows.bat`는 `py -3`, `py`, `python`, `python3` 순서로 Python을 탐색하고, `.venv` 가상환경을 만든 뒤 테스트와 PyInstaller 빌드를 실행합니다. 빌드 로그는 `build_logs\build_YYYYMMDD_HHMMSS.log`에 저장됩니다.

빌드 성공 후 실행 파일 위치:

```text
dist\PrivacyMasker\PrivacyMasker.exe
```

배포할 때는 `PrivacyMasker.exe`만 따로 복사하지 말고 `dist\PrivacyMasker` 폴더 전체를 압축해 전달하세요.

설치 프로그램 형태로 배포하려면 일반 exe 빌드 후 다음 명령을 실행하세요.

```powershell
build_installer.bat
```

성공하면 설치 파일 하나가 생성됩니다.

```text
dist\PrivacyMaskerSetup.exe
```

사용자가 `PrivacyMaskerSetup.exe`를 실행하면 `%LOCALAPPDATA%\Programs\PrivacyMasker`에 설치되고, 바탕화면과 시작 메뉴에 바로가기가 생성됩니다.

스캔 PDF OCR 기능을 사용하려면 Windows에 Tesseract OCR이 별도로 설치되어 있어야 합니다. Tesseract가 없어도 앱은 실행되며, XLSX, DOCX, 텍스트 PDF, HWPX 기능은 사용할 수 있습니다. 스캔 PDF 분석 시에는 Tesseract 설치 여부를 확인하고 안내 메시지를 표시합니다.

`Python`만 출력되고 빌드가 실패하면 Microsoft Store Python alias 문제일 수 있습니다. 이 경우 `README_RELEASE.md`의 Python 오류 해결 절차를 확인하세요.

Python이 설치되어 있지만 PATH만 꼬인 경우에는 `set PYTHON_EXE=파이썬실행파일경로`로 직접 지정한 뒤 `build_windows.bat`를 실행할 수 있습니다.

배포, 오류 해결, 스모크 테스트 절차는 `README_RELEASE.md`를 참고하세요.
