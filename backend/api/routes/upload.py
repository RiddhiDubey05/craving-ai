import os
import uuid
import time
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.s3_service import s3_service
from backend.services.embedding_service import embedding_service
from backend.models.schemas import ImageUploadResponse
from backend.utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["Upload"])

# Ensure directory for caching uploaded image embeddings exists
CACHE_DIR = os.path.join("data", "embeddings")
os.makedirs(CACHE_DIR, exist_ok=True)


@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    Upload a food image, store it in S3 (or local folder fallback),
    generate a multimodal embedding, and cache the embedding for query retrieval.
    """
    start_time = time.time()
    
    # Validate file type
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file."
        )

    try:
        # Read file bytes
        contents = await file.read()
        
        # Reset file pointer for S3 upload
        await file.seek(0)
        
        # Upload image (returns public S3 URL or local static URL)
        s3_url = s3_service.upload_image(file.file, file.filename, content_type)
        
        # Generate image embedding
        app_logger.info(f"Generating embedding for uploaded image: {file.filename}")
        embedding = embedding_service.get_image_embedding(contents)
        
        # Generate unique image ID and save embedding to disk cache
        image_id = str(uuid.uuid4())
        cache_path = os.path.join(CACHE_DIR, f"{image_id}.json")
        with open(cache_path, "w") as f:
            json.dump({
                "s3_url": s3_url,
                "embedding": embedding,
                "filename": file.filename
            }, f)
            
        latency = (time.time() - start_time) * 1000
        app_logger.info(f"Successfully processed image upload in {latency:.2f}ms. ID: {image_id}")
        
        return ImageUploadResponse(
            image_id=image_id,
            s3_url=s3_url,
            embedding_dim=len(embedding),
            latency_ms=latency
        )
        
    except Exception as e:
        app_logger.error(f"Error processing image upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload and process image: {str(e)}"
        )
