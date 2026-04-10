# 외부 크론 연동 가이드

GitHub Actions의 `schedule`이 원하는 시간에 정확히 돌지 않을 때는 외부 크론 서비스가 GitHub API를 호출해서 `Update Menu Board` 워크플로우를 실행할 수 있습니다.

## 1. 현재 워크플로우

- 저장소: `lky8783-dot/today-menu`
- 워크플로우 파일: `.github/workflows/update-menu.yml`
- 지원 트리거:
  - `workflow_dispatch`
  - `repository_dispatch` (`event_type: update-menu`)
  - `schedule`

## 2. GitHub 토큰 만들기

GitHub에서 Personal Access Token을 하나 만듭니다.

- 권장 타입: `Fine-grained token`
- 대상 저장소: `today-menu`
- 필요한 권한:
  - `Actions: Read and write`
  - `Contents: Read and write`
  - `Metadata: Read-only`

## 3. 외부 크론 서비스 예시

추천:

- [cron-job.org](https://cron-job.org)

시간은 한국시간 기준으로 아래 6개를 등록합니다.

- 평일 09:10
- 평일 09:40
- 평일 10:10
- 평일 10:40
- 평일 11:10
- 평일 11:40

## 4. repository_dispatch 호출 URL

```text
https://api.github.com/repos/lky8783-dot/today-menu/dispatches
```

## 5. 요청 헤더

```text
Accept: application/vnd.github+json
Authorization: Bearer <YOUR_GITHUB_TOKEN>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
User-Agent: today-menu-cron
```

## 6. 요청 Body

```json
{
  "event_type": "update-menu"
}
```

## 7. curl 예시

```bash
curl -X POST "https://api.github.com/repos/lky8783-dot/today-menu/dispatches" \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR_GITHUB_TOKEN>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -H "User-Agent: today-menu-cron" \
  -d "{\"event_type\":\"update-menu\"}"
```

## 8. PowerShell 예시

```powershell
$headers = @{
  Accept = "application/vnd.github+json"
  Authorization = "Bearer <YOUR_GITHUB_TOKEN>"
  "X-GitHub-Api-Version" = "2022-11-28"
  "User-Agent" = "today-menu-cron"
}

$body = @{
  event_type = "update-menu"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://api.github.com/repos/lky8783-dot/today-menu/dispatches" `
  -Method Post `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

## 9. cron-job.org 등록 팁

- Method: `POST`
- URL: `https://api.github.com/repos/lky8783-dot/today-menu/dispatches`
- Request body: `{"event_type":"update-menu"}`
- Request headers:
  - `Accept: application/vnd.github+json`
  - `Authorization: Bearer <YOUR_GITHUB_TOKEN>`
  - `X-GitHub-Api-Version: 2022-11-28`
  - `Content-Type: application/json`
  - `User-Agent: today-menu-cron`

## 10. 확인 방법

외부 크론이 정상 호출되면 Actions 탭에서 `Update Menu Board`가 아래처럼 보입니다.

- event: `repository_dispatch`
- conclusion: `success`

## 11. 권장 운영 방식

가장 안정적인 방식은 아래 둘을 같이 두는 것입니다.

1. GitHub `schedule` 유지
2. 외부 크론으로 `repository_dispatch` 추가

이렇게 하면 GitHub 내장 스케줄이 누락되더라도 외부 크론이 보완해 줍니다.
