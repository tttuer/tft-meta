"""DB 데이터 확인 스크립트"""
import asyncio
import sys
from datetime import date, timedelta

from sqlalchemy import select, func, cast
from sqlalchemy.types import Date

from app.database import AsyncSessionLocal
from app.models.match_raw import MatchRaw
from app.models.comp import Comp


async def check_data():
    """DB에 저장된 데이터 확인"""
    print("=" * 60)
    print("TFT Meta Advisor - DB 데이터 확인")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # 1. match_raw 테이블 확인
        result = await session.execute(select(func.count(MatchRaw.match_id)))
        total_matches = result.scalar()
        print(f"\n📊 match_raw 테이블:")
        print(f"  - 총 매치 수: {total_matches}")

        if total_matches > 0:
            # 날짜별 매치 수
            result = await session.execute(
                select(
                    cast(MatchRaw.collected_at, Date).label("date"),
                    func.count(MatchRaw.match_id).label("count")
                )
                .group_by(cast(MatchRaw.collected_at, Date))
                .order_by(cast(MatchRaw.collected_at, Date).desc())
            )
            print(f"\n  날짜별 매치 수:")
            for row in result:
                print(f"    - {row.date}: {row.count}개 매치")

            # 리전별 매치 수
            result = await session.execute(
                select(
                    MatchRaw.region,
                    func.count(MatchRaw.match_id).label("count")
                )
                .group_by(MatchRaw.region)
            )
            print(f"\n  리전별 매치 수:")
            for row in result:
                print(f"    - {row.region}: {row.count}개 매치")

            # 패치별 매치 수
            result = await session.execute(
                select(
                    MatchRaw.patch_version,
                    func.count(MatchRaw.match_id).label("count")
                )
                .group_by(MatchRaw.patch_version)
            )
            print(f"\n  패치별 매치 수:")
            for row in result:
                print(f"    - {row.patch_version}: {row.count}개 매치")

            # 오늘 수집된 데이터의 총 참가자 수
            today = date.today()
            result = await session.execute(
                select(MatchRaw).where(
                    cast(MatchRaw.collected_at, Date) == today
                )
            )
            today_matches = result.scalars().all()
            if today_matches:
                total_participants = sum(len(m.participants) for m in today_matches)
                print(f"\n  오늘({today}) 데이터:")
                print(f"    - 매치 수: {len(today_matches)}")
                print(f"    - 총 참가자 수: {total_participants}")

        # 2. comps 테이블 확인
        result = await session.execute(select(func.count(Comp.id)))
        total_comps = result.scalar()
        print(f"\n📊 comps 테이블:")
        print(f"  - 총 컴프 수: {total_comps}")

        if total_comps > 0:
            result = await session.execute(
                select(Comp)
                .order_by(Comp.win_rate.desc())
                .limit(5)
            )
            comps = result.scalars().all()
            print(f"\n  상위 5개 컴프:")
            for i, comp in enumerate(comps, 1):
                print(f"    {i}. {comp.name}")
                print(f"       - 티어: {comp.tier}")
                print(f"       - 승률: {comp.win_rate:.2%}")
                print(f"       - TOP4: {comp.top4_rate:.2%}")
                print(f"       - 샘플: {comp.sample_count}개")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_data())
    sys.exit(0)
