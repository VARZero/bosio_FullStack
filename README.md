# BOSIO Full Stack

PYNQ-Z2에서 BOSIO의 세 시스템을 함께 실행하기 위한 통합 저장소입니다.
기본 구면 타일 셀 분할도는 `M=32`입니다.

| 구성 요소 | 역할 |
|---|---|
| `bosio_OutputCore` | 정이십면체 프레임버퍼, 자세 투영, HDMI 출력 RTL |
| `bosio_SphericalWM` | 센서 허브, 드라이버, 구면 윈도우 데몬과 IPC |
| `BoAYO` | 시선 중심 런처, UI와 직접 구면 장면 합성 |

```text
GY-521 + PYNQ 버튼
        |
        v
BoAYO UI -> SphericalWM scene-stream -> OutputCore -> HDMI
                 |                         |
                 +-- IPC/서비스           +-- FPGA 투영/AA
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

1. SphericalWM 소프트웨어와 BS24 bitstream을 보드 임시 디렉터리에 전송합니다.
2. PYNQ-Z2에서 C++/NEON 합성기를 빌드합니다.
3. systemd 데몬을 설치하고 부팅 자동 실행을 활성화합니다.
4. BoAYO를 배포하고 런처를 scene-stream 소유자로 실행합니다.
5. 출력 코어, 센서, AA와 장면 소유권을 검사합니다.

Vivado에서 RTL을 다시 빌드하려면 `components/bosio_OutputCore`와
`components/bosio_SphericalWM/hw/scripts`를 사용합니다. 기본 통합 실행은
SphericalWM에 포함된 검증 완료 bitstream을 사용합니다.

## 보드 조작

- BTN0: 시선으로 포커스된 항목 선택 또는 드래그
- BTN1: 런처를 현재 시선 위치로 재배치
- GY-521: yaw·pitch·roll을 AXI4-Stream으로 출력 코어에 전달

## 라이선스

통합 스크립트는 Apache License 2.0입니다. 각 서브모듈의 소스는 해당 저장소의
라이선스를 따릅니다.
