"""
Quick smoke test for Riot API integration.
Run: uv run python test_riot_api.py

Requires RIOT_API_KEY set in .env
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.services.riot_api import get_challenger_summoners, get_match_ids


async def main():
    print("Fetching KR Challenger summoners...")
    summoners = await get_challenger_summoners("kr")
    print(f"  Found {len(summoners)} challengers")

    if summoners:
        # Get PUUID of first summoner via summoner-v4 (just show first entry)
        first = summoners[0]
        print(f"  First summoner: {first.get('summonerName', first.get('summonerId'))}")
        puuid = first.get("puuid")
        if puuid:
            print(f"  Fetching match IDs for puuid: {puuid[:20]}...")
            match_ids = await get_match_ids(puuid, region="kr", count=5)
            print(f"  Match IDs: {match_ids}")
        else:
            print("  No PUUID in entry (need summoner-v4 lookup for full flow)")
    else:
        print("  No summoners returned (check RIOT_API_KEY)")


if __name__ == "__main__":
    asyncio.run(main())
