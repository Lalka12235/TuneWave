import uuid
from pathlib import Path

from app.domain.interfaces.avatar_storage_gateway import AvatarStorageGateway
from app.config.settings import settings


class LocalAvatarStorageGateway(AvatarStorageGateway):

    def _mkdir_avatar(self) -> None:
        settings.avatar.AVATARS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        return

    def _generate_avatar_url(self,unique_filename: Path) -> str:
        base_url = f"{settings.BASE_URL}/avatars/{unique_filename}"
        return base_url

    def _parse_filename_for_avatar(self,filename: str) -> tuple[Path,Path]:
        file_extension = filename.split(".")[-1] if "." in filename else "png"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = settings.avatar.AVATARS_STORAGE_DIR / unique_filename
        return file_path,unique_filename

    def save_avatar(self,content: bytes,filename: str) -> str | None:
        file_path = None
        try:
            self._mkdir_avatar()
            file_path,unique_filename = self._parse_filename_for_avatar(filename)
            with open(file_path, "wb") as f:
                f.write(content)
            return self._generate_avatar_url(unique_filename)
        except Exception:
            if file_path.exists():
                file_path.unlink()

    def delete_avatar(self,avatar_url: str) -> bool:
        unique_filename = avatar_url.split()[-1]
        filepath = settings.avatar.AVATARS_STORAGE_DIR / unique_filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False