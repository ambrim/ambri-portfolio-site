import boto3
import os
from clients.kb_client import KnowledgeBaseClient
from strands.models import BedrockModel

def create_boto3_session():
  return boto3.Session(
      aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
      aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
      region_name=os.getenv("AWS_REGION"),
  )

def create_bedrock_model() -> BedrockModel:
  session = create_boto3_session()

  bedrock_model = BedrockModel(
      model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
      boto_session=session
  )

  return bedrock_model

def create_kb_client() -> KnowledgeBaseClient:
  session = create_boto3_session()

  kb_client = KnowledgeBaseClient(
      knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
      boto_session=session,
      region_name=os.getenv("AWS_REGION"),
  )

  return kb_client

# Singleton instance (shared everywhere)
kb_client_singleton = create_kb_client()
