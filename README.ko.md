# 🛠️ mcp-micro-shell

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/MCP-1.27.1+-orange.svg?style=for-the-badge&logo=modelcontextprotocol&logoColor=white" alt="MCP Version">
  <img src="https://img.shields.io/badge/powered%20by-uv-purple.svg?style=for-the-badge&logo=astral&logoColor=white" alt="Powered by UV">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>격리된 파일 조작과 안전한 터미널 실행 환경을 제공하는 초경량, 고성능의 MCP(Model Context Protocol) 서버입니다.</strong>
</p>

<p align="center">
  간결한 Flat Layout 구조로 완벽히 최적화되어 있으며, <a href="https://github.com/astral-sh/uv"><b>uv</b></a>를 기반으로 작동하여 <code>uvx</code>를 통한 글로벌 호출 및 즉각적인 실행을 지원합니다.
</p>

---

## 🌟 주요 특징

* **⚡ 번개처럼 빠른 구동:** 불필요한 깊이의 폴더 없이 핵심 파일만으로 설계되어 `uv` 가상환경 내에서 대기시간 없이 즉시 실행됩니다.
* **🛡️ 강력한 격리 보안 (샌드박스):** 파일 읽기/쓰기 및 터미널 명령어 실행은 오직 사전에 승인된 격리 워크스페이스 디렉토리(`MCP_MICRO_SHELL_WORKSPACE`) 안에서만 제한적으로 일어나며, 상위 폴더 탈출 경로 공격(`../`)을 강력하게 차단합니다.
* **🔌 멀티 트랜스포트 지원:**
  * **Stdio (기본값):** 로컬 데스크톱 클라이언트(Cursor, Claude Desktop, cl0w 등)와의 유기적이고 고속인 표준 I/O 통신방식입니다.
  * **SSE (Server-Sent Events):** Starlette 및 Uvicorn 기반의 웹서버를 기동하여 원격 네트워크에서 접속 가능하게 합니다.
* **⚙️ 깔끔한 로그 출력:** 서버 작동 중 발생하는 모든 시스템 로그는 온전히 `stderr`로만 출력되므로, 표준 출력(`stdout`) 통신 채널에 로그 메시지가 섞여 JSON-RPC 통신을 방해하지 않습니다.

---

## 📂 프로젝트 구조

필요 없는 구조를 걷어내고 결집도가 극대화된 파이썬 패키지 구조로 간결화했습니다:
```text
mcp-micro-shell/
├── pyproject.toml              # 프로젝트 빌드 및 실행 메타데이터 (Hatchling)
├── README.md                   # 영어 공식 설명서
├── README.ko.md                # 한국어 공식 설명서
├── uv.lock                     # 종속성 잠금 파일
└── mcp_micro_shell/            # 핵심 파이썬 패키지 폴더
    ├── __init__.py             # 버전 선언
    ├── __main__.py            # 모듈 실행 진입점 (python -m)
    └── server.py              # 통합 서버 엔진 및 도구 바인딩 파일
```

---

## 🛠️ 제공되는 도구 (Tools)

모든 도구는 지정된 워크스페이스 루트 경로를 기준으로 절대/상대 경로를 자동 확인 및 병합하여 검증을 거친 후 안전하게 처리합니다.

| 도구명 | 전달 인자 | 상세 설명 |
| :--- | :--- | :--- |
| **`execute_command`** | `command` (문자열, **필수**),<br>`cwd` (문자열, 선택),<br>`timeout` (정수형, 선택) | 지정된 워크스페이스(또는 내부 하위 디렉토리) 내에서 터미널 명령어를 안전하게 수행합니다. 시스템 PATH 환경변수를 그대로 유지하여 편리하게 개발 도구들을 사용할 수 있습니다. |
| **`get_current_directory`** | 없음 | 현재 활성화되어 강제 적용 중인 격리 워크스페이스의 전체 경로를 반환합니다. |
| **`read_file`** | `path` (문자열, **필수**) | 지정된 워크스페이스 범위 내에 위치한 텍스트 파일 내용을 안전하게 읽습니다. 외부 경로를 우회하는 파일 접근은 철저히 접근이 거부됩니다. |
| **`write_file`** | `path` (문자열, **필수**),<br>`content` (문자열, **필수**) | 지정된 워크스페이스 내부에 텍스트 파일을 작성합니다. 지정한 하위 폴더 경로가 없다면 자동으로 중간 폴더들을 생성해 줍니다. 마찬가지로 범위 외의 쓰기 시도는 전면 차단됩니다. |

---

## 🚀 시작하기

### 사전 요구사항
시스템에 `uv`가 설치되어 있어야 합니다. 설치되지 않은 경우 아래 명령어로 간편하게 설치할 수 있습니다:

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🏃 서버 실행하기

### 1. Stdio 모드 (기본값)
대부분의 로컬 데스크톱 AI 도구 연동에 적합한 표준 입출력 방식입니다.
```bash
uv run mcp-micro-shell
```

### 2. SSE 모드 (웹 API 방식)
원격 환경이나 서버 연동이 필요한 경우 유용한 HTTP SSE 서버 기동 방식입니다.
```bash
uv run mcp-micro-shell --transport sse --host 127.0.0.1 --port 8000
```

---

## 🔌 MCP 클라이언트와 연동 (`mcp.json`)

Claude Desktop, Cursor, cl0w 등의 클라이언트 환경에서 `uvx`를 통해 로컬에 연동하려면 아래 설정을 클라이언트 JSON 파일에 추가해 줍니다.

```json
{
  "mcpServers": {
    "mcp-micro-shell": {
      "command": "uvx",
      "args": [
        "--from",
        "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell",
        "mcp-micro-shell"
      ],
      "env": {
        "MCP_MICRO_SHELL_WORKSPACE": "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell\\workspace"
      }
    }
  }
}
```
*(추후 PyPI에 패키지를 공식 게시한 후에는 `--from` 로컬 경로 인자를 생략하고 간편히 클라우드로부터 바로 내려받아 연동할 수 있게 됩니다.)*
