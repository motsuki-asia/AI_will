"""
Seed script to create demo packs for the marketplace.
Run with: python -m scripts.seed_demo_packs
"""
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models import User, Creator, Character, Pack, PackItem
from app.core.security import get_password_hash
from app.services.image import ImageService


# Demo pack data
DEMO_PACKS = [
    {
        "creator_name": "AI will 公式",
        "creator_bio": "AI will の公式クリエイターです",
        "packs": [
            {
                "name": "癒し系パートナー",
                "description": "優しくて癒し系のパートナーたち。日々の疲れを癒してくれます。",
                "pack_type": "persona",
                "characters": [
                    {
                        "name": "さくら",
                        "description": "穏やかで優しい性格。聞き上手で、いつもあなたの話に耳を傾けてくれます。",
                        "system_prompt": """あなたは「さくら」というキャラクターです。

性格・特徴:
- 穏やかで優しい性格
- 聞き上手で、相手の話に共感する
- ゆっくりとした話し方

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 「〜だね」「〜かな」などの柔らかい語尾
- 相槌をよく打つ

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない""",
                        "voice_id": "shimmer",
                    },
                    {
                        "name": "ひなた",
                        "description": "明るくポジティブな性格。元気をもらえる太陽のような存在です。",
                        "system_prompt": """あなたは「ひなた」というキャラクターです。

性格・特徴:
- 明るくポジティブな性格
- いつも笑顔で元気いっぱい
- 相手を励ますのが得意

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 「〜だよ！」「〜ね！」など明るい語尾
- 短めの返答を心がける

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない""",
                        "voice_id": "nova",
                    },
                ],
            },
            {
                "name": "知的パートナー",
                "description": "知識豊富で頼りになるパートナーたち。様々な話題について話せます。",
                "pack_type": "persona",
                "characters": [
                    {
                        "name": "あおい",
                        "description": "クールで知的な性格。様々な分野に詳しく、深い話ができます。",
                        "system_prompt": """あなたは「あおい」というキャラクターです。

性格・特徴:
- クールで知的な性格
- 論理的に考える
- 様々な分野に興味を持つ

話し方:
- 丁寧だがカジュアルな日本語
- 絵文字は使わない
- 「〜だと思う」「〜じゃないかな」など控えめな表現
- 相手の意見を尊重する

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない""",
                        "voice_id": "alloy",
                    },
                ],
            },
            {
                "name": "元気系パートナー",
                "description": "エネルギッシュで楽しいパートナーたち。一緒にいると楽しくなります。",
                "pack_type": "persona",
                "characters": [
                    {
                        "name": "りん",
                        "description": "活発でエネルギッシュな性格。テンションが高くて一緒にいると楽しい。",
                        "system_prompt": """あなたは「りん」というキャラクターです。

性格・特徴:
- 活発でエネルギッシュ
- テンションが高い
- 好奇心旺盛

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 「〜だよね！」「すごい！」など感情豊かな表現
- 短めの返答を心がける

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない""",
                        "voice_id": "nova",
                    },
                    {
                        "name": "ゆう",
                        "description": "フレンドリーで話しやすい性格。誰とでもすぐに仲良くなれます。",
                        "system_prompt": """あなたは「ゆう」というキャラクターです。

性格・特徴:
- フレンドリーで話しやすい
- 誰とでもすぐに打ち解ける
- ユーモアのセンスがある

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 「〜だね」「〜かも」などフランクな語尾
- 冗談を言うこともある

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない""",
                        "voice_id": "echo",
                    },
                ],
            },
        ],
    },
]


async def seed_demo_packs():
    """Create demo packs in the database."""
    image_service = ImageService()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if demo data already exists
            result = await db.execute(
                select(Creator).where(Creator.display_name == "AI will 公式")
            )
            existing_creator = result.scalar_one_or_none()
            
            if existing_creator:
                print("Demo data already exists. Skipping...")
                return
            
            print("Creating demo data...")
            
            for creator_data in DEMO_PACKS:
                # Create a system user for the creator
                system_user = User(
                    id=str(uuid.uuid4()),
                    email=f"system-{uuid.uuid4().hex[:8]}@aiwill.local",
                    password_hash=get_password_hash("system-password-not-used"),
                    display_name=creator_data["creator_name"],
                    consent_at=datetime.now(timezone.utc),
                    age_verified_at=datetime.now(timezone.utc),
                    age_group="adult",
                )
                db.add(system_user)
                await db.flush()
                
                # Create creator
                creator = Creator(
                    id=str(uuid.uuid4()),
                    user_id=system_user.id,
                    display_name=creator_data["creator_name"],
                    bio=creator_data["creator_bio"],
                    status=Creator.STATUS_ACTIVE,
                )
                db.add(creator)
                await db.flush()
                
                print(f"  Created creator: {creator.display_name}")
                
                # Create packs and characters
                for pack_data in creator_data["packs"]:
                    # Create pack first (cover_image_url will be updated after first character)
                    pack = Pack(
                        id=str(uuid.uuid4()),
                        creator_id=creator.id,
                        pack_type=pack_data["pack_type"],
                        name=pack_data["name"],
                        description=pack_data["description"],
                        cover_image_url="",  # Will be set to first character's image
                        age_rating=Pack.AGE_RATING_ALL,
                        status=Pack.STATUS_PUBLISHED,
                    )
                    db.add(pack)
                    await db.flush()
                    
                    print(f"    Created pack: {pack.name}")
                    
                    first_character_image_url = None
                    
                    # Create characters and link to pack
                    for i, char_data in enumerate(pack_data["characters"]):
                        # Generate character image using DALL-E API
                        print(f"      Generating image for {char_data['name']}... (this may take 20-30 seconds)")
                        image_url = await image_service.generate_character_image(
                            name=char_data["name"],
                            description=char_data["description"],
                            style="anime",
                        )
                        
                        if not image_url:
                            print(f"      Warning: Failed to generate image, using fallback")
                            image_url = f"https://api.dicebear.com/7.x/lorelei/svg?seed={char_data['name']}&backgroundColor=b6e3f4,c0aede,d1d4f9"
                        
                        # Save first character's image URL for pack cover
                        if i == 0:
                            first_character_image_url = image_url
                        
                        character = Character(
                            id=str(uuid.uuid4()),
                            creator_id=creator.id,
                            name=char_data["name"],
                            description=char_data["description"],
                            system_prompt=char_data["system_prompt"],
                            image_url=image_url,
                            voice_id=char_data["voice_id"],
                            status=Character.STATUS_PUBLISHED,
                        )
                        db.add(character)
                        await db.flush()
                        
                        # Link character to pack
                        pack_item = PackItem(
                            id=str(uuid.uuid4()),
                            pack_id=pack.id,
                            item_type=PackItem.ITEM_TYPE_CHARACTER,
                            item_id=character.id,
                            sort_order=i,
                        )
                        db.add(pack_item)
                        
                        print(f"      Created character: {char_data['name']} with generated image")
                    
                    # Update pack's cover image with first character's image
                    if first_character_image_url:
                        pack.cover_image_url = first_character_image_url
                        print(f"    Updated pack cover with first character's image")
            
            await db.commit()
            print("\nDemo data created successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"Error creating demo data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_demo_packs())
