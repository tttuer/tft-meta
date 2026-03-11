"""
GitHub Copilot OAuth 토큰 발급 스크립트 (최초 1회 실행)
발급된 gho_ 토큰을 .env의 GITHUB_TOKEN에 저장하세요.

실행: uv run python get_copilot_token.py
"""
import time

import httpx

# GitHub Copilot VSCode 확장의 OAuth App Client ID
CLIENT_ID = "Iv1.b507a08c87ecfe98"


def main():
    with httpx.Client(timeout=10.0) as client:
        # 1. 디바이스 코드 요청
        r = client.post(
            "https://github.com/login/device/code",
            data={"client_id": CLIENT_ID, "scope": "read:user"},
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        data = r.json()

        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data.get("interval", 5)

        print(f"\n1. 브라우저에서 열기: {verification_uri}")
        print(f"2. 코드 입력: {user_code}")
        print("\n입력 완료 후 대기 중...\n")

        # 2. 토큰 폴링
        while True:
            time.sleep(interval)
            r = client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            result = r.json()

            if "access_token" in result:
                token = result["access_token"]
                print(f"✅ 토큰 발급 성공!\n")
                print(f"GITHUB_TOKEN={token}")
                print(f"\n위 값을 backend/.env 에 저장하세요.")
                return

            error = result.get("error")
            if error == "authorization_pending":
                print("대기 중...")
            elif error == "slow_down":
                interval += 5
            else:
                print(f"오류: {result}")
                return


if __name__ == "__main__":
    main()
