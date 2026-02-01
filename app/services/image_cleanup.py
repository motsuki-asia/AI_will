"""Image Cleanup Service - Delete expired scene images"""
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_message import ConversationMessage


class ImageCleanupService:
    """Service for cleaning up expired images"""

    # 画像保存ディレクトリ
    IMAGES_DIR = Path("static/images/characters")

    async def cleanup_expired_images(self, db: AsyncSession) -> int:
        """
        期限切れの画像メッセージを削除する

        Returns:
            削除した画像の数
        """
        now = datetime.now(timezone.utc)

        # 期限切れの画像メッセージを取得
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.content_type == "image")
            .where(ConversationMessage.expires_at.isnot(None))
            .where(ConversationMessage.expires_at < now)
        )
        expired_messages = list(result.scalars().all())

        deleted_count = 0
        for message in expired_messages:
            # ファイルを削除
            if message.image_url:
                file_path = self._get_file_path(message.image_url)
                if file_path and file_path.exists():
                    try:
                        os.remove(file_path)
                        print(f"Deleted image file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete image file {file_path}: {e}")

            # DBからメッセージを削除
            await db.delete(message)
            deleted_count += 1

        if deleted_count > 0:
            await db.commit()
            print(f"Cleaned up {deleted_count} expired images")

        return deleted_count

    def _get_file_path(self, image_url: str) -> Path | None:
        """画像URLからファイルパスを取得"""
        if not image_url:
            return None

        # /static/images/characters/scene_xxx.png -> static/images/characters/scene_xxx.png
        if image_url.startswith("/static/"):
            return Path(image_url[1:])  # 先頭の / を除去
        return None


async def run_cleanup_on_startup(db: AsyncSession):
    """アプリ起動時に実行するクリーンアップ"""
    service = ImageCleanupService()
    deleted = await service.cleanup_expired_images(db)
    if deleted > 0:
        print(f"Startup cleanup: Removed {deleted} expired images")
