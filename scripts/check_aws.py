#!/usr/bin/env python
import os
import sys
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Add project root to sys.path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from backend.config import get_settings
    settings = get_settings()
except ImportError:
    settings = None

def print_banner(title):
    print("=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

def main():
    print_banner("CravingAI AWS Service Validator")
    
    # 1. Read configuration
    print("[1] Verifying environment variable settings...")
    if not settings:
        print("  ❌ ERROR: Could not load backend configuration.")
        return
        
    aws_region = settings.aws_region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    s3_bucket = settings.s3_bucket_name
    bedrock_model = settings.bedrock_llm_model_id
    bedrock_emb_model = settings.bedrock_embedding_model_id
    
    print(f"  • Region: {aws_region}")
    print(f"  • S3 Bucket Target: {s3_bucket}")
    print(f"  • Bedrock LLM Model: {bedrock_model}")
    print(f"  • Bedrock Embedding Model: {bedrock_emb_model}")
    
    # Check AWS Access keys
    key_id = os.getenv("AWS_ACCESS_KEY_ID") or settings.aws_access_key_id
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or settings.aws_secret_access_key
    
    if not key_id or key_id == "your_access_key_here":
        print("  ⚠️ WARNING: AWS_ACCESS_KEY_ID is missing or set to placeholder.")
    if not secret_key or secret_key == "your_secret_key_here":
        print("  ⚠️ WARNING: AWS_SECRET_ACCESS_KEY is missing or set to placeholder.")

    # 2. Check S3 Access
    print("\n[2] Testing AWS S3 connection...")
    try:
        s3 = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=key_id if key_id != "your_access_key_here" else None,
            aws_secret_access_key=secret_key if secret_key != "your_secret_key_here" else None
        )
        # Try listing buckets or checking target bucket
        if s3_bucket:
            s3.head_bucket(Bucket=s3_bucket)
            print(f"  ✅ SUCCESS: Successfully accessed bucket '{s3_bucket}'!")
        else:
            s3.list_buckets()
            print("  ✅ SUCCESS: Connected to S3 (no specific bucket configured)!")
    except NoCredentialsError:
        print("  ❌ ERROR: AWS credentials not found.")
    except ClientError as ce:
        error_code = ce.response.get("Error", {}).get("Code")
        if error_code == "404":
            print(f"  ❌ ERROR: Bucket '{s3_bucket}' does not exist.")
        elif error_code == "403":
            print(f"  ❌ ERROR: Access denied to bucket '{s3_bucket}' (check permissions).")
        else:
            print(f"  ❌ ERROR: S3 client check failed: {ce}")
    except Exception as e:
        print(f"  ❌ ERROR: S3 connection failed: {e}")

    # 3. Check Bedrock Runtime Access
    print("\n[3] Testing AWS Bedrock Runtime connection...")
    try:
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=key_id if key_id != "your_access_key_here" else None,
            aws_secret_access_key=secret_key if secret_key != "your_secret_key_here" else None
        )
        
        # Test Embedding model
        print(f"  • Sending test request to embedding model: {bedrock_emb_model}...")
        import json
        emb_body = json.dumps({"inputText": "validation check"})
        
        # BedrockTitan multimodal embedding call format
        response = bedrock.invoke_model(
            modelId=bedrock_emb_model,
            contentType="application/json",
            accept="application/json",
            body=emb_body
        )
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        if embedding:
            print(f"  ✅ SUCCESS: Embedding generated! Dimensions: {len(embedding)}")
        else:
            print("  ❌ ERROR: Response body did not contain embedding vector.")
            
        # Test LLM converse API model
        print(f"  • Sending test query to LLM: {bedrock_model}...")
        messages = [{"role": "user", "content": [{"text": "Hello, answer in exactly three words."}]}]
        converse_response = bedrock.converse(
            modelId=bedrock_model,
            messages=messages,
            inferenceConfig={"maxTokens": 10, "temperature": 0.5}
        )
        answer = converse_response['output']['message']['content'][0]['text']
        print(f"  ✅ SUCCESS: LLM response: '{answer.strip()}'")

    except NoCredentialsError:
        print("  ❌ ERROR: AWS credentials not found.")
    except ClientError as ce:
        print(f"  ❌ ERROR: Bedrock model invocation denied or failed: {ce}")
    except Exception as e:
        print(f"  ❌ ERROR: Bedrock test failed: {e}")

    print("\n" + "=" * 60)
    print(" Validation check complete.".center(60))
    print("=" * 60)

if __name__ == "__main__":
    main()
