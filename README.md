# BOSIO Full Stack

PYNQ-Z2에서 BOSIO의 세 시스템을 함께 실행하기 위한 통합 저장소입니다.
기본 구면 타일 셀 분할도는 `M=16`입니다.

| 구성 요소 | 역할 |
|---|---|
| `bosio_OutputCore` | 정이십면체 프레임버퍼, 자세 투영, HDMI 출력 RTL |
| `bosio_SphericalWM` | 센서 허브, 드라이버, 구면 윈도우 데몬·IPC·창 합성 |
| `BoAYO` | 시선 중심 런처, 앱 SDK, 앱별 창 내용과 캡션 |

```text
GY-521 ─ AXI4-Stream 자세 ──────────────────> OutputCore
PYNQ 버튼 ─> SphericalWM 입력 ─> BoAYO 런처/앱 SDK
                                    |
                                    v
                            SphericalWM 구면 창 합성
                                    |
                                    v
                             OutputCore ─> HDMI
```

## 내려받기

```sh
git clone --recursive https://github.com/VARZero/bosio_FullStack.git
cd bosio_FullStack
python -m pip install -r requirements.txt
```

이미 일반 clone을 했다면 다음 명령으로 세 저장소를 받습니다.

```sh
git submodule update --init --recursive
```

## PYNQ-Z2 통합 실행

SSH 키를 사용할 수 있습니다. 암호 로그인이 필요하면 환경 변수로만 전달합니다.

```sh
export BOSIO_PYNQ_HOST=192.168.2.99
export BOSIO_PYNQ_USER=xilinx
export BOSIO_PYNQ_PASSWORD='your-password'

python scripts/bosio_stack.py deploy
python scripts/bosio_stack.py start
python scripts/bosio_stack.py status
```

Windows PowerShell에서는 다음과 같이 설정합니다.

```powershell
$env:BOSIO_PYNQ_HOST = "192.168.2.99"
$env:BOSIO_PYNQ_USER = "xilinx"
$env:BOSIO_PYNQ_PASSWORD = "your-password"
python scripts/bosio_stack.py deploy-start
```

`deploy-start`는 다음 작업을 순서대로 수행합니다.

1. SphericalWM 소프트웨어와 출력 bitstream을 보드에 전송합니다.
2. PYNQ-Z2에서 C++/NEON 합성기를 빌드하고 Bosio 서비스를 설치합니다.
3. BoAYo 런처, SDK, 앱 예제와 서비스 파일을 배포합니다.
4. BoAYo 런처를 Bosio 창으로 실행합니다.
5. 출력 코어·센서 상태와 런처 창 등록을 검사합니다.

설치된 `boayo-desktop.service`는 `bosio-window-manager.service` 뒤에 실행되며 두
서비스 모두 부팅 자동 시작으로 활성화됩니다.

Vivado에서 RTL을 다시 빌드하려면 `components/bosio_OutputCore`와
`components/bosio_SphericalWM/hw/scripts`를 사용합니다. 기본 통합 실행은
SphericalWM에 포함된 검증 완료 bitstream을 사용합니다.

## 보드 조작

- BTN0/BTN1: 유일한 런처 패널을 현재 시선 위치에 열기
- BTN2: 시선 위치를 클릭하거나 누른 채 창 캡션을 드래그; 패널 밖 클릭은 패널만 닫기
- GY-521: yaw·pitch·roll을 AXI4-Stream으로 출력 코어에 전달

전체 개발 소스는 세 구성 요소 저장소에 있습니다. 이 통합 저장소는 각 저장소의
검증된 커밋을 Git submodule로 고정하고, 보드 배포·실행 스크립트를 제공합니다.
새 복제에서는 `git clone --recursive` 또는 `git submodule update --init --recursive`를
사용해야 앱 SDK, 센서 허브 RTL, 출력 코어 RTL까지 내려받습니다.

BoAYo SDK 0.2.0은 `sdk.window_state(window)`로 구면 창 크기·고정 RGB 표면 크기·
포커스를 읽고, `sdk.poll_events()`에서 창별 `resize`/`focus` 이벤트를 제공합니다.
앱 구현 예제는 [BoAYo SDK 빠른 시작](components/BoAYO/docs/SDK_QUICKSTART.md)에 있습니다.

## 라이선스

통합 스크립트는 Apache License 2.0입니다. 각 서브모듈의 소스는 해당 저장소의
라이선스를 따릅니다.
