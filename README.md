# macOS tmux IME

한국어 입력 상태에서 tmux prefix를 누르면 ABC 입력기로 전환하는 작은 도구입니다.
Karabiner, Hammerspoon, Homebrew 패키지, 상주 프로세스, 손쉬운 사용 권한이 필요하지 않습니다.
실행 파일은 prefix를 누를 때만 실행됩니다. 기존 pane 이동 등의 단축키는 그대로 사용합니다.

## 준비

- macOS, tmux 3.2 이상, Ghostty 1.3 이상
- Xcode 또는 Apple Command Line Tools. 컴파일러가 없다면 `xcode-select --install`
- 시스템 설정 → 키보드 → 입력 소스에 **ABC**가 등록되어 있어야 합니다.

소스 폴더만 전달해도 사용할 수 있습니다. Apple Silicon과 Intel은 각자의 Mac에서 빌드합니다.
tmux 자체를 다시 빌드할 필요는 없습니다.

## 빌드 및 설치

이 폴더에서 실행합니다. Ctrl-A를 prefix로 사용하는 경우:

```sh
./build.sh
./install.sh --prefix C-a
```

tmux 기본 prefix인 Ctrl-B를 사용한다면 `./install.sh --prefix C-b`로 설치합니다.
설치 스크립트는 현재 Mac용으로 다시 빌드한 뒤 다음 파일을 설치합니다.

- `~/.local/bin/tmux-ime`
- `~/.config/tmux-ime/tmux.conf`
- `~/.config/tmux-ime/ghostty.conf`

다른 내용의 기존 파일은 `.bak.날짜.프로세스번호` 이름으로 백업합니다.
`~/.tmux.conf`와 Ghostty의 주 설정 파일은 직접 수정하지 않습니다.

먼저 조회 명령으로 ABC가 있는지 확인합니다. 조회는 입력기를 바꾸지 않습니다.

```sh
~/.local/bin/tmux-ime
~/.local/bin/tmux-ime --list
```

### 설정 연결

기존 설정을 백업한 뒤, `~/.tmux.conf`의 **기존 prefix 설정보다 뒤쪽**에 추가합니다.

```tmux
source-file ~/.config/tmux-ime/tmux.conf
```

Ghostty 설정 파일에 설치 스크립트가 출력한 `keybind` 행을 추가합니다. Ctrl-A의 예시는
아래와 같습니다(Ctrl-B는 `ctrl+KeyB=text:\x02`). macOS의 일반적인 설정 파일 위치는
`~/Library/Application Support/com.mitchellh.ghostty/config`이며,
Ghostty의 Open Configuration 메뉴로 실제 사용하는 파일을 열 수 있습니다.

```ini
keybind = ctrl+KeyA=text:\x01
```

tmux 설정을 다시 읽고, Ghostty의 Reload Configuration 메뉴(기본 Cmd-Shift-,)를 실행합니다.

```sh
tmux source-file ~/.tmux.conf
```

## 사용과 작동 방식

한국어 상태에서 **prefix → 원래 사용하던 명령 키**를 누릅니다.
예를 들어 Ctrl-A 사용자는 `Ctrl-A → h`로 pane을 이동할 수 있습니다.
단, `h/j/k/l` 이동은 원래 그 바인딩을 설정한 사용자에게만 해당합니다.
도구가 새로 추가하는 이동 단축키는 없습니다.

1. Ghostty가 물리 Ctrl-A 또는 Ctrl-B를 해당 ASCII 제어 문자로 전달합니다.
2. tmux가 입력기 전환 프로그램을 실행하고 종료를 기다립니다.
3. 기존 `prefix` 키 테이블에 진입해 다음 키를 처리합니다.

명령 후에도 ABC를 유지합니다. 다시 한국어를 쓰려면 평소처럼 직접 전환합니다.
prefix를 두 번 누르면 프로그램에 Ctrl-A/Ctrl-B가 한 번 전달됩니다.
일반 상태와 emacs/vi copy mode 모두 같은 prefix 진입을 지원합니다.
입력기 전환에 실패해도 prefix 명령은 계속 동작하며 상태줄에 오류를 표시합니다.

설정은 내장 prefix 인식을 `None`으로 바꾸고 키 바인딩으로 진입을 대신합니다.
따라서 `tmux show -gv prefix`의 출력이 `None`인 것은 정상입니다.
`send-prefix`나 `#{prefix}` 값을 직접 사용하는 별도 플러그인/바인딩은 이 구성을
인지하지 못할 수 있습니다. 제공한 두 번 누르기 바인딩은 `send-keys`를 사용합니다.

### 적용 범위와 한계

- **이 Mac에서 실행 중인 tmux**용입니다. SSH로 접속한 원격 tmux 서버에서 실행해도
  로컬 Mac의 입력기를 바꿀 수 없습니다. 설정을 원격 Linux 서버에 복사하지 마세요.
- 일반 셸에서는 입력기를 자동 전환하지 않습니다. Ghostty의 제어 문자 전달만 적용됩니다.
- 입력기 선택은 해당 macOS 로그인 세션에 영향을 줍니다. 원격 사용자가 이 Mac의 tmux에
  붙어서 prefix를 누르는 구성이나 여러 GUI 사용자가 공유하는 서버는 대상이 아닙니다.
- tmux가 기다리는 동안에도 IME가 이미 변환한 다음 글자를 되돌릴 수는 없습니다.
  매우 빠른 연속 입력과 한글 조합 중 입력은 실제 사용하는 macOS/입력기에서 확인하세요.
  이 도구는 전역 키 이벤트를 가로채거나 지연시키지 않습니다.

## 명령행 인터페이스

```sh
tmux-ime                                 # 현재 입력기 ID
tmux-ime --list                          # 선택 가능한 ID와 이름 (탭 구분)
tmux-ime com.apple.keylayout.ABC          # ABC 선택
tmux-ime --help
```

`~/.local/bin`이 PATH에 없다면 실행 파일의 전체 경로를 사용합니다.
전환 성공 시 출력 없이 0, 전환 실패 시 stderr 메시지와 1,
잘못된 인수에는 2를 반환합니다. 이미 선택된 입력기를 다시 선택하는 것은 무해합니다.
ABC가 아닌 영문 레이아웃을 쓰려면 `--list`로 ID를 확인하고 설치된 tmux 설정의
`com.apple.keylayout.ABC` 세 곳을 해당 ID로 바꿉니다.

## 확인

한국어 입력을 선택한 다음 아래 항목을 확인합니다.

- prefix → 방향키/숫자/창 생성 등 기존 명령
- 기존에 등록한 `h/j/k/l`, Shift-H/J/K/L, copy mode 진입 및 조작
- prefix 두 번 누르기
- 한글 조합 중 prefix: 글자가 유실되거나 다른 pane에 섞여 들어가지 않는지
- 빠른 prefix 연속 입력: 첫 명령이 누락되지 않는지

개발용 자동 테스트는 Python 3가 있을 때 다음으로 실행합니다.
별도 tmux 소켓과 임시 디렉터리만 사용하며 실제 입력기를 전환하지 않습니다.

```sh
python3 tests/test_integration.py
```

## 제거 및 원래 prefix 복원

두 주 설정 파일에서 추가한 `source-file`/`keybind` 행을 제거하고 Ghostty 설정을
다시 읽습니다. tmux 설정에서 행을 지우는 것만으로 현재 서버의 바인딩이 복원되지는 않습니다.

Ctrl-A 구성의 기본 바인딩 복원 예시:

```sh
tmux unbind-key -T root C-a
tmux bind-key -T copy-mode C-a send-keys -X start-of-line
tmux unbind-key -T copy-mode-vi C-a
tmux set-option -g prefix C-a
tmux bind-key -T prefix C-a send-prefix
```

Ctrl-B 구성의 기본 바인딩 복원 예시:

```sh
tmux unbind-key -T root C-b
tmux bind-key -T copy-mode C-b send-keys -X cursor-left
tmux bind-key -T copy-mode-vi C-b send-keys -X page-up
tmux set-option -g prefix C-b
tmux bind-key -T prefix C-b send-prefix
```

원래 해당 키나 `prefix2`를 따로 변경했다면 기본값 대신 백업의 바인딩을 복원합니다.
설정 연결을 제거한 후 설치된 실행 파일과 `~/.config/tmux-ime`의 제공 파일도 삭제할 수 있습니다.
실행 중인 tmux 세션을 종료할 필요는 없습니다.

## 친구에게 전달하기

```sh
./package.sh
```

`dist/macos-tmux-ime-src.tar.gz`가 생성됩니다. 소스, 빌드·설치 스크립트,
설정 예시, 테스트, 이 README와 라이선스를 포함하며 실행 파일과 개인 설정은 제외합니다.
친구는 압축을 풀고 `./install.sh --prefix C-b`(또는 `C-a`)부터 진행하면 됩니다.

개발용 설치 테스트에서는 `TMUX_IME_DESTDIR=/임시/경로 ./install.sh`로 설치를
임시 디렉터리에 한정할 수 있습니다. 생성된 설정의 실행 경로는 실제 사용자의 HOME 기준입니다.
