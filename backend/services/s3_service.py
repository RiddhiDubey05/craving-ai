import os
import uuid
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

from backend.config import get_settings
from backend.utils.logger import app_logger

settings = get_settings()


class S3Service:
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.use_fallback = False
        
        # Check if AWS credentials are placeholders or empty
        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
            or not settings.aws_secret_access_key
        )

        if is_placeholder:
            app_logger.warning("AWS S3 credentials not configured. Falling back to local storage.")
            self.use_fallback = True
            self.s3_client = None
            # Ensure local image folder exists
            self.local_dir = os.path.join("data", "images")
            os.makedirs(self.local_dir, exist_ok=True)
        else:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region,
                )
                app_logger.info("AWS S3 Client successfully initialized.")
            except Exception as e:
                app_logger.error(f"Failed to initialize S3 client: {e}. Falling back to local storage.")
                self.use_fallback = True
                self.s3_client = None
                self.local_dir = os.path.join("data", "images")
                os.makedirs(self.local_dir, exist_ok=True)

    def upload_image(self, file_obj: BinaryIO, filename: str, content_type: str = "image/jpeg") -> str:
        """
        Uploads a file to S3 (or local mock folder as a fallback).
        Returns the public URL of the uploaded image.
        """
        unique_filename = f"{uuid.uuid4()}_{filename}"

        if self.use_fallback:
            local_path = os.path.join(self.local_dir, unique_filename)
            try:
                with open(local_path, "wb") as f:
                    f.write(file_obj.read())
                # Return a local mock URL path
                app_logger.info(f"Local fallback: Saved file to {local_path}")
                # Use a relative/mock path that the API can serve
                return f"/static/images/{unique_filename}"
            except Exception as e:
                app_logger.error(f"Failed to save file locally: {e}")
                raise RuntimeError(f"Failed to store image: {e}")

        # Real AWS S3 Upload
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    "ContentType": content_type,
                    # Optional: "ACL": "public-read" if bucket allows it
                }
            )
            s3_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{unique_filename}"
            app_logger.info(f"Successfully uploaded {filename} to S3: {s3_url}")
            return s3_url
        except NoCredentialsError:
            app_logger.error("AWS S3 credentials not found during upload.")
            raise RuntimeError("AWS S3 credentials not found.")
        except ClientError as e:
            app_logger.error(f"S3 client error: {e}")
            raise RuntimeError(f"S3 upload failed: {e}")
        except Exception as e:
            app_logger.error(f"Unexpected error during S3 upload: {e}")
            raise RuntimeError(f"Image upload failed: {e}")


# Singleton instance
s3_service = S3Service()
