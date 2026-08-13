import os

from clients.retrieval.base import RetrievalClient
from clients.retrieval.local_keyword_client import LocalKeywordRetrievalClient
from clients.retrieval.upstash_vector_client import UpstashVectorRetrievalClient


def create_retrieval_client() -> RetrievalClient:
    provider = os.getenv("RETRIEVAL_PROVIDER", "local").lower()

    if provider == "upstash":
        return UpstashVectorRetrievalClient(
            rest_url=os.getenv("UPSTASH_VECTOR_REST_URL", ""),
            rest_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN", ""),
            namespace=os.getenv("UPSTASH_VECTOR_NAMESPACE"),
        )

    if provider == "aws":
        import boto3

        from clients.kb_client import KnowledgeBaseClient
        from clients.retrieval.aws_kb_client import AwsKnowledgeBaseRetrievalClient

        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        return AwsKnowledgeBaseRetrievalClient(
            KnowledgeBaseClient(
                knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
                boto_session=session,
                region_name=os.getenv("AWS_REGION"),
            )
        )

    if provider == "local":
        return LocalKeywordRetrievalClient(
            data_dir=os.getenv("LOCAL_RAG_DATA_DIR", "data"),
        )

    raise ValueError(f"Unsupported RETRIEVAL_PROVIDER: {provider}")


retrieval_client_singleton = create_retrieval_client()
