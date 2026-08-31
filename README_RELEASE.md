# PrivacyMasker Windows 배포 안내

이 문서는 Python을 모르는 Windows 사용자가 `PrivacyMasker.exe`를 실행할 수 있도록 배포 파일을 만드는 절차와 배포 전 점검 항목을 정리합니다.

## 빠른 빌드 순서

1. Windows 탐색기에서 `privacy_masker` 폴더를 엽니다.
2. 주소창을 클릭하고 `cmd`를 입력한 뒤 Enter를 누릅니다.
3. 열린 CMD 창에서 다음 명령을 실행합니다.

```cmd
build_windows.bat
```

빌드가 성공하면 실행 파일은 다음 위치에 생성됩니다.

```text
dist\PrivacyMasker\PrivacyMasker.exe
```

배치 파일은 자동으로 다음 작업을 수행합니다.

- 프로젝트 루트 확인
- 사용 가능한 Python 탐색: `py -3`, `py`, `python`, `python3`
- PATH가 꼬인 경우 일반 Python 설치 경로도 확인
- `.venv` 가상환경 생성 또는 기존 가상환경 사용
- `pip`, `requirements.txt`, `requirements-dev.txt` 설치
- `pytest -q` 실행
- `build`, `dist` 폴더 정리
- PyInstaller `onedir` 빌드 실행
- `dist\PrivacyMasker\PrivacyMasker.exe` 존재 여부 확인
- `build_logs\build_YYYYMMDD_HHMMSS.log`에 빌드 로그 저장

테스트를 임시로 건너뛰어 빌드 문제만 확인하려면 CMD에서 다음처럼 실행합니다.

```cmd
set SKIP_TESTS=1
build_windows.bat
```

배포 전에는 반드시 `SKIP_TESTS` 없이 다시 빌드하세요.

## 1. 배포 방식

기본 배포 방식은 PyInstaller `onedir`입니다.

권장 이유:

- PySide6, PyMuPDF, openpyxl, python-docx 같은 문서 처리 의존성이 많아 문제 추적이 쉽습니다.
- 실행 파일과 내부 라이브러리가 폴더 안에 함께 들어 있어 누락 파일을 확인하기 쉽습니다.
- OCR 기능은 별도 Tesseract 설치가 필요하므로 `onefile`보다 운영 안내가 명확합니다.

## 2. 빌드 준비와 CMD 여는 방법

가장 쉬운 방법은 탐색기 주소창을 사용하는 것입니다.

1. `privacy_masker` 폴더를 엽니다.
2. 탐색기 주소창에 `cmd`를 입력합니다.
3. Enter를 누르면 해당 폴더에서 CMD가 열립니다.

직접 이동하려면 CMD에서 다음처럼 실행합니다.

```cmd
cd "C:\Users\덕유중\Documents\DATA MASKING\privacy_masker"
```

권장 Python 버전은 Python 3.11 또는 3.12입니다.

Python 상태를 먼저 확인하려면 CMD에서 다음 명령을 실행합니다.

```cmd
python --version
py --version
where python
where py
```

## 3. 빌드 방법

가장 쉬운 방법은 배치 파일을 실행하는 것입니다.

```cmd
build_windows.bat
```

배치 파일이 수행하는 일:

- 사용 가능한 Python 실행기 탐색
- `.venv` 가상환경 생성 또는 재사용
- `pip` 업데이트
- `requirements.txt` 설치
- `requirements-dev.txt` 설치
- `pytest -q` 실행
- 기존 `build`, `dist` 폴더 정리
- `python -m PyInstaller privacy_masker.spec --clean -y` 실행
- 성공 시 `dist\PrivacyMasker` 위치 안내
- 전체 로그를 `build_logs` 폴더에 저장

수동 빌드 명령은 다음과 같습니다.

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m PyInstaller privacy_masker.spec --clean -y
```

`py` 명령이 정상인 환경에서는 다음처럼 직접 빌드할 수도 있습니다.

```cmd
py -m pip install --upgrade pip
py -m pip install -r requirements-dev.txt
py -m pytest -q
py -m PyInstaller privacy_masker.spec --clean -y
```

## 4. 실행 방법

빌드 성공 후 다음 파일을 실행합니다.

```powershell
dist\PrivacyMasker\PrivacyMasker.exe
```

사용자에게 배포할 때는 `dist\PrivacyMasker` 폴더 전체를 압축해 전달하세요. `PrivacyMasker.exe`만 따로 빼서 실행하면 `_internal` 폴더의 라이브러리를 찾지 못해 실행되지 않을 수 있습니다.

## 5. 권장 배포 폴더 구조

PyInstaller `onedir` 결과는 보통 다음 구조입니다.

```text
PrivacyMasker_Release/
  PrivacyMasker.exe
  _internal/
  README.md
  README_RELEASE.md
  sample_files/
  docs/
```

실제 PyInstaller 출력 폴더는 다음 위치입니다.

```text
dist/PrivacyMasker/
```

`sample_files`와 `docs`는 필요할 때 배포자가 직접 추가해도 됩니다.

## 6. Tesseract OCR 안내

스캔 PDF OCR 기능을 사용하려면 Windows에 Tesseract OCR이 별도로 설치되어 있어야 합니다.

- Tesseract가 없어도 앱 자체는 실행됩니다.
- Tesseract가 없으면 스캔 PDF 분석 시 설치 필요 안내가 표시되어야 합니다.
- 텍스트 PDF, XLSX, DOCX, HWPX 기능은 Tesseract 없이도 사용할 수 있습니다.
- Tesseract 설치 후에도 인식되지 않으면 `tesseract.exe` 경로가 Windows `PATH` 환경 변수에 등록되어 있는지 확인하세요.
- OCR은 누락 또는 오탐 가능성이 있으므로 검토 화면에서 결과를 반드시 확인해야 합니다.

## 7. Python 오류 해결

### Python을 찾을 수 없음

CMD에서 다음 명령을 실행해 상태를 확인하세요.

```cmd
python --version
py --version
where python
where py
```

둘 다 실패하면 Python 3.11 또는 3.12를 설치해야 합니다. 설치할 때 `Add python.exe to PATH`를 체크하세요. 설치 후에는 기존 CMD 창을 닫고 새 CMD 창을 열어 다시 실행하세요.

### `Python`만 출력되고 실패함

`python --version` 또는 빌드 중 `Python` 한 단어만 출력되고 실패하면 Microsoft Store Python alias 문제일 가능성이 있습니다.

해결 방법:

- `py --version`이 동작하는지 확인합니다.
- `py`가 동작하면 `build_windows.bat`가 자동으로 `py -3` 또는 `py`를 우선 사용합니다.
- Windows 설정 > 앱 > 고급 앱 설정 > 앱 실행 별칭에서 `python.exe`, `python3.exe` 별칭을 끕니다.
- 그래도 안 되면 Python 3.11 또는 3.12를 다시 설치하고 `Add python.exe to PATH`를 체크합니다.

Python이 설치되어 있지만 PATH만 잘못된 경우에는 직접 경로를 지정할 수 있습니다.

```cmd
set PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
build_windows.bat
```

Python 3.11을 설치했다면 `Python312` 대신 `Python311` 경로를 사용하세요.

### Python 환경 진단 스크립트

가상환경이 만들어진 뒤 다음 명령으로 주요 패키지와 PyInstaller 상태를 확인할 수 있습니다.

```cmd
.venv\Scripts\python.exe tools\check_python_env.py
```

## 8. 보안 안내

- 이 프로그램은 로컬 PC에서 파일을 처리합니다.
- 외부 서버, 외부 API, 클라우드 변환 서비스로 문서를 전송하지 않습니다.
- 검토 화면에는 개인정보 원문이 표시되므로 화면 공유, 캡처, 원격 지원 중 노출에 주의하세요.
- CSV 로그에는 `original_text`, `masked_text`, 탐지된 개인정보 원문을 저장하지 않습니다.
- 파일명 자체에 개인정보가 있으면 파일명이 로그에 남을 수 있으므로 운영 파일명에도 개인정보를 넣지 않는 것을 권장합니다.
- OCR 결과는 누락될 수 있으므로 사용자가 직접 검토해야 합니다.
- 구형 HWP 파일은 안정 지원 대상이 아니며 HWPX로 변환 후 처리해야 합니다.
- 법적·행정적 비식별화 책임은 최종 사용자가 결과 파일을 열어 확인한 뒤 판단해야 합니다.
- 결과 파일을 외부에 배포하기 전 반드시 직접 열어 마스킹 상태를 확인하세요.

## 9. 배포 전 스모크 테스트 체크리스트

| ID | 확인 항목 | 예상 결과 | Pass/Fail |
|---|---|---|---|
| S-01 | `PrivacyMasker.exe` 더블클릭 실행 | 첫 화면이 열린다 |  |
| S-02 | 파일 선택 화면 표시 | 파일 추가 버튼과 목록이 보인다 |  |
| S-03 | XLSX 샘플 파일 선택 | 파일 목록에 표시된다 |  |
| S-04 | DOCX 샘플 파일 선택 | 파일 목록에 표시된다 |  |
| S-05 | 텍스트 PDF 샘플 파일 선택 | 파일 목록에 표시된다 |  |
| S-06 | HWPX 샘플 파일 선택 | 파일 목록에 표시된다 |  |
| S-07 | 저장 폴더 선택 | 다음 단계로 진행 가능하다 |  |
| S-08 | 분석 실행 | 탐지 결과가 검토 표에 표시된다 |  |
| S-09 | `masked_text` 직접 수정 | 수정한 값이 표에 유지된다 |  |
| S-10 | 마스킹 사본 저장 | `masked_원본파일명` 결과 파일이 생성된다 |  |
| S-11 | 원본 파일 확인 | 원본 파일 내용이 바뀌지 않았다 |  |
| S-12 | CSV 로그 생성 확인 | 로그 파일이 생성된다 |  |
| S-13 | CSV 로그 내용 확인 | 개인정보 원문과 마스킹 문자열이 없다 |  |
| S-14 | HWP 파일 선택 | 안정 지원 대상 아님 안내가 표시된다 |  |
| S-15 | Tesseract 미설치 상태에서 스캔 PDF 분석 | OCR 설치 필요 안내가 표시된다 |  |
| S-16 | 저장 폴더 열기 버튼 | Windows 탐색기가 열린다 |  |
| S-17 | 같은 이름으로 재저장 | `_2`, `_3` 번호가 붙는다 |  |

## 10. 자주 발생하는 문제

### 앱이 실행되지 않음

- Windows 보안 경고에서 실행 차단 여부를 확인하세요.
- 압축 파일 안에서 바로 실행하지 말고 먼저 압축을 해제하세요.
- `dist\PrivacyMasker` 폴더 내부의 `_internal` 폴더를 삭제하거나 이동하지 않았는지 확인하세요.

### pip 설치 실패

- 인터넷 연결이 가능한지 확인하세요.
- 회사/학교 보안망에서 PyPI 접속이 막혀 있는지 확인하세요.
- `build_logs` 폴더의 최신 로그 파일에서 실패 패키지 이름을 확인하세요.

### pytest 실패

- 테스트 실패 상태에서는 배포 빌드를 중단하는 것이 정상입니다.
- 최신 로그 파일에서 실패한 테스트 이름을 확인하세요.
- 빌드 동작만 임시 확인하려면 `set SKIP_TESTS=1` 후 다시 실행할 수 있지만, 배포 전에는 테스트를 다시 통과시켜야 합니다.

### PyInstaller 실패

- `.venv\Scripts\python.exe -m PyInstaller --version`으로 설치 여부를 확인하세요.
- `requirements-dev.txt` 설치가 성공했는지 확인하세요.
- 최신 `build_logs\build_*.log` 파일에서 실패 단계와 오류 메시지를 확인하세요.

### `styles.qss`를 찾을 수 없음

- `privacy_masker.spec`의 `datas`에 `ui/styles.qss`가 포함되어 있는지 확인하세요.
- `dist\PrivacyMasker\_internal` 또는 PyInstaller 내부 데이터에 `ui\styles.qss`가 포함되는지 확인하세요.

### PySide6 플랫폼 플러그인 오류

- 가상환경에서 `PySide6`를 다시 설치한 뒤 재빌드하세요.
- `requirements-dev.txt` 설치 후 `pyinstaller privacy_masker.spec`를 다시 실행하세요.
- 문제가 계속되면 디버깅용으로 spec의 `console=True` 빌드를 임시로 사용해 콘솔 오류를 확인하세요.

### Tesseract를 찾을 수 없음

- Tesseract OCR 설치 여부를 확인하세요.
- `tesseract.exe`가 Windows `PATH`에 등록되어 있는지 확인하세요.
- Tesseract가 없어도 텍스트 PDF, XLSX, DOCX, HWPX 기능은 사용할 수 있습니다.

### PDF 처리 오류

- 암호가 걸린 PDF인지 확인하세요.
- 손상된 PDF인지 확인하세요.
- 스캔 PDF라면 Tesseract 설치 여부를 확인하세요.

### 저장 실패

- 저장 폴더에 쓰기 권한이 있는지 확인하세요.
- 결과 파일이 Excel, Word, PDF 뷰어 등 다른 프로그램에서 열려 있는지 확인하세요.
- 같은 이름 파일이 있으면 프로그램은 자동으로 `_2`, `_3` 번호를 붙입니다.

### HWP 파일 처리 불가

- 구형 HWP는 안정 지원 대상이 아닙니다.
- 한글 프로그램에서 HWPX로 변환한 뒤 다시 시도하세요.

## 11. 빌드 로그와 실패 정보

`build_windows.bat`는 모든 주요 출력과 명령 결과를 `build_logs` 폴더에 저장합니다.

예:

```text
build_logs\build_20260629_153000.log
```

빌드가 실패하면 CMD 화면과 로그에서 다음 정보를 확인하세요.

- 실패 단계
- 사용한 Python 명령
- Python 버전
- pip 버전
- PyInstaller 버전
- 로그 파일 위치
- 다음에 실행할 진단 명령

## 12. 디버깅용 빌드

기본 spec은 `console=False`입니다. 실행 오류를 콘솔에서 확인하려면 `privacy_masker.spec`의 `EXE(..., console=False, ...)`를 임시로 `console=True`로 바꾼 뒤 다시 빌드하세요.

배포용으로 되돌릴 때는 다시 `console=False`로 설정하세요.

## 13. 알려진 한계

- 코드 서명 인증서가 없으면 Windows SmartScreen 또는 백신 경고가 표시될 수 있습니다.
- 스캔 PDF OCR 품질은 원본 이미지 품질과 Tesseract 언어 데이터에 영향을 받습니다.
- DOCX 복잡한 서식은 일부 단순화될 수 있습니다.
- HWPX의 이미지, 첨부 파일, 복잡한 메타데이터 안 개인정보는 완전 보장하지 않습니다.
- 구형 HWP 완전 지원, 설치 마법사, 자동 업데이트는 이번 배포 범위가 아닙니다.

## 14. 설치 프로그램 형태로 배포하기

`dist\PrivacyMasker` 폴더 전체를 직접 압축해서 전달하는 대신, 설치용 실행 파일 하나를 만들 수 있습니다.

먼저 일반 앱 배포물을 만든 뒤:

```bat
build_windows.bat
```

설치 프로그램을 만듭니다:

```bat
build_installer.bat
```

성공하면 다음 파일이 생성됩니다:

```text
dist\PrivacyMaskerSetup.exe
```

사용자는 `PrivacyMaskerSetup.exe`를 실행하면 됩니다. 설치 프로그램은 현재 사용자 계정 아래에 앱을 설치합니다:

```text
%LOCALAPPDATA%\Programs\PrivacyMasker
```

설치 후 바탕화면과 시작 메뉴에 `PrivacyMasker` 바로가기가 생성됩니다. 이 방식은 관리자 권한 설치가 아니라 사용자별 설치입니다.

주의:

- `PrivacyMaskerSetup.exe`는 내부에 `dist\PrivacyMasker` 배포물을 포함합니다.
- 설치 파일을 새로 만들기 전에는 반드시 최신 앱을 `build_windows.bat`로 먼저 빌드하세요.
- 코드 서명 인증서가 없으면 Windows SmartScreen 또는 백신 경고가 표시될 수 있습니다.
- 설치 프로그램은 Tesseract OCR을 포함하지 않습니다. 스캔 PDF OCR 기능을 쓰려면 사용자 PC에 Tesseract OCR이 별도로 필요합니다.
