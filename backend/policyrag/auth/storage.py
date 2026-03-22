import logging

from policyrag.config import settings

logger = logging.getLogger(__name__)

_supabase_client = None


def get_supabase_client():
    """Get or create a Supabase client using the service role key."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("Supabase URL or service role key not configured; storage disabled")
            return None
        from supabase import create_client
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


def upload_to_storage(user_id: str, doc_id: str, filename: str, content: bytes) -> str:
    """Upload a file to Supabase Storage. Returns the storage path."""
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase client not available; skipping storage upload")
        return ""

    path = f"{user_id}/{doc_id}/{filename}"
    bucket = settings.SUPABASE_STORAGE_BUCKET

    try:
        client.storage.from_(bucket).upload(
            path,
            content,
            file_options={"content-type": "application/pdf"},
        )
        logger.info(f"Uploaded {path} to bucket {bucket}")
        return path
    except Exception as e:
        logger.error(f"Failed to upload {path} to storage: {e}")
        raise


def delete_from_storage(path: str) -> None:
    """Remove a file from Supabase Storage."""
    client = get_supabase_client()
    if not client or not path:
        return

    bucket = settings.SUPABASE_STORAGE_BUCKET
    try:
        client.storage.from_(bucket).remove([path])
        logger.info(f"Deleted {path} from bucket {bucket}")
    except Exception as e:
        logger.error(f"Failed to delete {path} from storage: {e}")
