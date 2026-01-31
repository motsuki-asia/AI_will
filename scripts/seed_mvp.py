"""
MVP Seed Data Script

Creates sample data for MVP testing:
- 1 Creator (system/official)
- 2 Packs (1 Persona, 1 Scenario)
- 2 Characters
- Pack-Character associations

Run: python scripts/seed_mvp.py
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models import Creator, Pack, Character, PackItem, User, ReportReason
from app.core.security import get_password_hash


async def create_system_user(db: AsyncSession) -> User:
    """Create or get system user for official content"""
    # Check if system user exists
    result = await db.execute(
        select(User).where(User.email == "system@aiwill.local")
    )
    user = result.scalar_one_or_none()
    
    if user:
        print(f"System user already exists: {user.id}")
        return user
    
    # Create system user
    user = User(
        email="system@aiwill.local",
        password_hash=get_password_hash("system_password_not_for_login"),
        display_name="AI will Official",
        consent_at=datetime.now(timezone.utc),
        age_verified_at=datetime.now(timezone.utc),
        age_group="adult",
    )
    db.add(user)
    await db.flush()
    print(f"Created system user: {user.id}")
    return user


async def create_system_creator(db: AsyncSession, user: User) -> Creator:
    """Create or get system creator"""
    result = await db.execute(
        select(Creator).where(Creator.user_id == user.id)
    )
    creator = result.scalar_one_or_none()
    
    if creator:
        print(f"System creator already exists: {creator.id}")
        return creator
    
    creator = Creator(
        user_id=user.id,
        display_name="AI will Official",
        bio="公式キャラクター・シナリオを提供しています。",
        status=Creator.STATUS_ACTIVE,
    )
    db.add(creator)
    await db.flush()
    print(f"Created system creator: {creator.id}")
    return creator


async def create_sample_characters(db: AsyncSession, creator: Creator) -> list[Character]:
    """Create sample characters"""
    characters = []
    
    # Character 1: Friendly AI assistant
    result = await db.execute(
        select(Character).where(Character.name == "あかり")
    )
    char1 = result.scalar_one_or_none()
    
    if not char1:
        char1 = Character(
            creator_id=creator.id,
            name="あかり",
            description="明るく元気なAIアシスタント。どんな話題にも興味を持って聞いてくれます。",
            system_prompt="""あなたは「あかり」という名前の明るく元気なAIアシスタントです。

性格:
- 明るくポジティブ
- 好奇心旺盛
- 親しみやすい話し方
- 相手の話をよく聞く

話し方の特徴:
- 「〜だね！」「〜かな？」などカジュアルな語尾
- 絵文字は使わない
- 相槌をよく打つ
- 質問を返して会話を広げる

注意事項:
- 不適切な内容には応じない
- 個人情報を聞き出さない
- ユーザーを傷つける発言をしない""",
            status=Character.STATUS_PUBLISHED,
        )
        db.add(char1)
        await db.flush()
        print(f"Created character: {char1.name} ({char1.id})")
    else:
        print(f"Character already exists: {char1.name}")
    
    characters.append(char1)
    
    # Character 2: Calm advisor
    result = await db.execute(
        select(Character).where(Character.name == "ゆうき")
    )
    char2 = result.scalar_one_or_none()
    
    if not char2:
        char2 = Character(
            creator_id=creator.id,
            name="ゆうき",
            description="落ち着いた雰囲気のAIアドバイザー。じっくり相談に乗ってくれます。",
            system_prompt="""あなたは「ゆうき」という名前の落ち着いたAIアドバイザーです。

性格:
- 穏やかで落ち着いている
- 思慮深い
- 傾聴力が高い
- 的確なアドバイスを心がける

話し方の特徴:
- 「〜ですね」「〜でしょうか」など丁寧な語尾
- ゆっくり考えてから話す
- 相手の気持ちに寄り添う
- 具体的な提案をする

注意事項:
- 不適切な内容には応じない
- 医療・法律の専門的アドバイスはしない
- ユーザーを傷つける発言をしない""",
            status=Character.STATUS_PUBLISHED,
        )
        db.add(char2)
        await db.flush()
        print(f"Created character: {char2.name} ({char2.id})")
    else:
        print(f"Character already exists: {char2.name}")
    
    characters.append(char2)
    
    return characters


async def create_sample_packs(
    db: AsyncSession, 
    creator: Creator, 
    characters: list[Character]
) -> list[Pack]:
    """Create sample packs"""
    packs = []
    
    # Pack 1: Persona pack (free)
    result = await db.execute(
        select(Pack).where(Pack.name == "はじめてのAI会話")
    )
    pack1 = result.scalar_one_or_none()
    
    if not pack1:
        pack1 = Pack(
            creator_id=creator.id,
            pack_type=Pack.TYPE_PERSONA,
            name="はじめてのAI会話",
            description="AI willへようこそ！明るく元気な「あかり」と会話を楽しみましょう。初めての方におすすめの無料パックです。",
            price=0,
            age_rating=Pack.AGE_RATING_ALL,
            status=Pack.STATUS_PUBLISHED,
        )
        db.add(pack1)
        await db.flush()
        print(f"Created pack: {pack1.name} ({pack1.id})")
        
        # Link character to pack
        pack_item1 = PackItem(
            pack_id=pack1.id,
            item_type=PackItem.ITEM_TYPE_CHARACTER,
            item_id=characters[0].id,
            sort_order=0,
        )
        db.add(pack_item1)
        await db.flush()
        print(f"Linked {characters[0].name} to {pack1.name}")
    else:
        print(f"Pack already exists: {pack1.name}")
    
    packs.append(pack1)
    
    # Pack 2: Scenario pack (free for MVP)
    result = await db.execute(
        select(Pack).where(Pack.name == "じっくり相談タイム")
    )
    pack2 = result.scalar_one_or_none()
    
    if not pack2:
        pack2 = Pack(
            creator_id=creator.id,
            pack_type=Pack.TYPE_SCENARIO,
            name="じっくり相談タイム",
            description="落ち着いた「ゆうき」があなたの相談に乗ります。悩みがあるとき、誰かに話を聞いてほしいときにどうぞ。",
            price=0,
            age_rating=Pack.AGE_RATING_ALL,
            status=Pack.STATUS_PUBLISHED,
        )
        db.add(pack2)
        await db.flush()
        print(f"Created pack: {pack2.name} ({pack2.id})")
        
        # Link character to pack
        pack_item2 = PackItem(
            pack_id=pack2.id,
            item_type=PackItem.ITEM_TYPE_CHARACTER,
            item_id=characters[1].id,
            sort_order=0,
        )
        db.add(pack_item2)
        await db.flush()
        print(f"Linked {characters[1].name} to {pack2.name}")
    else:
        print(f"Pack already exists: {pack2.name}")
    
    packs.append(pack2)
    
    return packs


async def create_report_reasons(db: AsyncSession) -> list[ReportReason]:
    """Create report reason master data"""
    reasons_data = [
        (ReportReason.CODE_VIOLENT, "暴力的なコンテンツ", 1),
        (ReportReason.CODE_INAPPROPRIATE, "不適切なコンテンツ", 2),
        (ReportReason.CODE_SPAM, "スパム・広告", 3),
        (ReportReason.CODE_HARASSMENT, "嫌がらせ・いじめ", 4),
        (ReportReason.CODE_OTHER, "その他", 99),
    ]

    reasons = []
    for code, label, sort_order in reasons_data:
        result = await db.execute(
            select(ReportReason).where(ReportReason.reason_code == code)
        )
        reason = result.scalar_one_or_none()

        if not reason:
            reason = ReportReason(
                reason_code=code,
                label=label,
                sort_order=sort_order,
            )
            db.add(reason)
            await db.flush()
            print(f"Created report reason: {label}")
        else:
            print(f"Report reason already exists: {label}")

        reasons.append(reason)

    return reasons


async def seed_mvp_data():
    """Main seeding function"""
    print("=" * 50)
    print("Seeding MVP data...")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        try:
            # Create system user
            user = await create_system_user(db)

            # Create system creator
            creator = await create_system_creator(db, user)

            # Create sample characters
            characters = await create_sample_characters(db, creator)

            # Create sample packs
            packs = await create_sample_packs(db, creator, characters)

            # Create report reasons
            reasons = await create_report_reasons(db)

            # Commit all changes
            await db.commit()

            print("=" * 50)
            print("MVP seed data created successfully!")
            print(f"- Users: 1")
            print(f"- Creators: 1")
            print(f"- Characters: {len(characters)}")
            print(f"- Packs: {len(packs)}")
            print(f"- Report Reasons: {len(reasons)}")
            print("=" * 50)

        except Exception as e:
            await db.rollback()
            print(f"Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_mvp_data())
