# GitHub 업로드 가이드 (처음이신 분용)

이 문서는 **The Steady Compass** 프로젝트를 GitHub에 처음 올리는 분을 위한 단계별 안내입니다.

---

## 준비물

- **Git**이 PC에 설치되어 있어야 합니다.
- **GitHub 계정**이 있어야 합니다. (없다면 [github.com](https://github.com) 에서 무료 가입)

---

## Part 1. Git 설치 확인

1. **Windows 키**를 누르고 `PowerShell` 이라고 입력합니다.
2. **Windows PowerShell** 앱을 클릭해 실행합니다.
3. 검은 창(또는 파란 창)이 열리면 아래를 **그대로** 입력하고 **Enter**를 누릅니다.

   ```
   git --version
   ```

4. `git version 2.xx.x` 처럼 버전이 나오면 **설치된 것**입니다.
5. 버전이 안 나오고 "알 수 없는 명령" 비슷한 메시지가 나오면, [git-scm.com](https://git-scm.com/download/win) 에서 Windows용 Git을 다운로드해 설치한 뒤, **PowerShell을 다시 열고** 3번부터 다시 합니다.

---

## Part 2. 프로젝트 폴더로 이동하기

1. PowerShell이 열린 상태에서 아래를 **한 줄씩** 입력합니다. (따옴표 포함, 그대로 복사해서 붙여넣기 하세요.)

   ```
   cd "c:\Users\bluem\OneDrive\Documents\Business\Life\toojar\the steady compass"
   ```

2. **Enter**를 누릅니다.
3. 아무 에러 메시지가 없으면 **성공**입니다. 이제 이 폴더가 "현재 작업 폴더"가 됩니다.

---

## Part 3. GitHub에서 저장소(Repository) 만들기

1. 웹 브라우저에서 [https://github.com](https://github.com) 로 이동합니다.
2. 로그인합니다. (계정이 없으면 **Sign up**으로 가입)
3. 오른쪽 위 **+** 버튼을 클릭합니다.
4. **New repository**를 클릭합니다.
5. 다음처럼 입력/선택합니다.
   - **Repository name:** `the-steady-compass` (또는 원하는 이름, 띄어쓰기 없이)
   - **Description:** 비워 두거나 "The Steady Compass web app" 등 입력
   - **Public** 선택
   - **"Add a README file"** 체크 **하지 않습니다** (로컬 프로젝트를 올릴 것이므로)
6. 맨 아래 **Create repository** 버튼을 클릭합니다.
7. 새 페이지가 열리면 **저장소 주소**를 복사해 둡니다.
   - 초록색 **Code** 버튼 옆 주소: `https://github.com/본인아이디/the-steady-compass.git`
   - 이 주소는 나중에 사용합니다.

---

## Part 4. Git 초기화 및 첫 커밋 (PowerShell에서)

PowerShell에서 **아래 명령을 한 줄씩** 입력하고, 각 줄마다 **Enter**를 누릅니다.

### 4-1. Git 저장소로 만들기

```
git init
```

- 의미: "이 폴더를 Git이 관리하는 프로젝트로 만든다."
- `Initialized empty Git repository...` 라고 나오면 성공입니다.

### 4-2. 파일들을 스테이징(올릴 목록에 넣기)

```
git add .
```

- 의미: "이 폴더 안의 모든 파일을 다음 커밋에 포함시킨다."
- 마침표(.)는 "현재 폴더 전체"를 뜻합니다.
- `.gitignore` 덕분에 `secrets.toml` 같은 비밀 파일은 자동으로 제외됩니다.

### 4-3. 상태 확인 (선택이지만 권장)

```
git status
```

- **초록색**으로 나오는 파일들이 "커밋될 파일"입니다.
- 여기 목록에 **secrets.toml** 이 있으면 안 됩니다. 있다면 `.gitignore`에 `.streamlit/secrets.toml` 이 들어 있는지 확인하세요.
- `app.py`, `pages/`, `components/` 등이 보이면 정상입니다.

### 4-4. 첫 커밋(저장) 만들기

```
git commit -m "Initial commit: The Steady Compass web app"
```

- 의미: "지금까지 스테이징한 내용을 하나의 '저장 단위(커밋)'로 남긴다."
- `-m "..."` 안의 글자는 이 커밋에 대한 설명입니다. 원하면 다른 문구로 바꿔도 됩니다.
- `1 file changed` 또는 `XX files changed` 라고 나오면 성공입니다.

---

## Part 5. GitHub 저장소와 연결하고 올리기

### 5-1. 원격 저장소 주소 등록

아래에서 **본인 GitHub 아이디**와 **저장소 이름**만 바꿔서 입력합니다.

```
git remote add origin https://github.com/본인아이디/the-steady-compass.git
```

예: GitHub 아이디가 `johndoe` 라면  
`git remote add origin https://github.com/johndoe/the-steady-compass.git`

- **한 번만** 하면 됩니다. "origin"이라는 이름으로 GitHub 주소가 저장됩니다.

### 5-2. 기본 브랜치 이름을 main으로

```
git branch -M main
```

- GitHub 기본 브랜치 이름이 `main` 이므로 맞춰 주는 단계입니다.

### 5-3. GitHub로 올리기 (Push)

```
git push -u origin main
```

- 의미: "지금까지 만든 커밋을 GitHub의 `origin` 저장소의 `main` 브랜치로 보낸다."
- **Enter**를 누르면 다음 중 하나가 됩니다.

---

## Part 6. 로그인 / 인증

`git push` 를 처음 하면 **로그인**이 필요합니다.

### 방법 A: 브라우저가 열리는 경우

- GitHub 로그인 창이 뜨면 **브라우저에서 로그인**하면 됩니다.
- 로그인 후 PowerShell로 돌아오면 자동으로 업로드가 진행됩니다.

### 방법 B: 사용자 이름과 비밀번호를 묻는 경우

- **Username:** GitHub 아이디
- **Password:** 여기서는 **비밀번호가 아니라 Personal Access Token(PAT)** 를 넣어야 합니다.

#### Personal Access Token 만드는 방법

1. GitHub 웹사이트에서 로그인 후, 오른쪽 위 **프로필 사진** 클릭 → **Settings**.
2. 왼쪽 맨 아래 **Developer settings** 클릭.
3. **Personal access tokens** → **Tokens (classic)** 클릭.
4. **Generate new token** → **Generate new token (classic)** 클릭.
5. **Note:** 예) `steady-compass-upload`
6. **Expiration:** 90 days 또는 No expiration (본인 선택)
7. **Select scopes:** **repo** 에 체크 (전체 체크됨).
8. 맨 아래 **Generate token** 클릭.
9. 나오는 **토큰 문자열**을 **한 번만** 보여 주므로, 반드시 **복사**해서 안전한 곳에 붙여 넣어 둡니다.
10. PowerShell에서 **Password:** 라고 나오면, 여기에 **그 토큰을 붙여넣기** 합니다. (입력해도 화면에는 안 보입니다. 그대로 붙여넣고 Enter)

---

## Part 7. 성공 확인

- `git push` 후에 `Writing objects: 100%` 같은 진행 표시가 나오고, 에러 없이 끝나면 **성공**입니다.
- GitHub 웹사이트에서 해당 저장소 페이지를 새로고침하면 **파일들이 보입니다**.

---

## 자주 나오는 메시지

| 메시지 | 의미 / 해결 |
|--------|-------------|
| `fatal: not a git repository` | `git init` 을 하지 않았거나, 잘못된 폴더에 있습니다. Part 2로 이동한 뒤 `git init` 부터 다시 하세요. |
| `Authentication failed` | Username/Password(토큰)가 틀렸습니다. 토큰을 새로 만들거나, 브라우저 로그인 방식으로 다시 시도해 보세요. |
| `failed to push` / `rejected` | GitHub에 이미 README 등이 있는 경우일 수 있습니다. `git pull origin main --rebase` 후 다시 `git push -u origin main` 해 보세요. |
| `secrets.toml` 이 목록에 보임 | `.gitignore` 파일에 `.streamlit/secrets.toml` 이 한 줄 있는지 확인하고, 있다면 `git rm --cached .streamlit/secrets.toml` 후 다시 `git add .` 와 `git commit` 하세요. |

---

## 요약: 복사해서 쓸 명령어 순서

(본인 아이디와 저장소 이름으로 바꾼 뒤, 한 줄씩 실행)

```
cd "c:\Users\bluem\OneDrive\Documents\Business\Life\toojar\the steady compass"
git init
git add .
git status
git commit -m "Initial commit: The Steady Compass web app"
git remote add origin https://github.com/본인아이디/the-steady-compass.git
git branch -M main
git push -u origin main
```

이후 로그인/토큰 입력만 완료하면 GitHub에 업로드가 끝납니다.
