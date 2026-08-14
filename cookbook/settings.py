"""
App Settings
============

Shared runtime objects for the platform.
"""

from agno.db.postgres import PostgresDb
from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAILike
from agno.vectordb.pgvector import PgVector, SearchType
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    base_url: str = Field(..., description="模型服务的地址")
    api_key: str = Field(..., description="模型服务授权的api key")
    model: str = Field(..., description="模型")
    embedder: str = Field(..., description="Embedding模型")

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    def create_model(self) -> OpenAILike:
        """Fresh model instance per agent — avoids shared-state footguns."""
        return OpenAILike(
            base_url=openai_settings.base_url,
            api_key=openai_settings.api_key,
            id=openai_settings.model,
        )

    def create_embedder(self) -> OpenAIEmbedder:
        return OpenAIEmbedder(
            base_url=openai_settings.base_url,
            api_key=openai_settings.api_key,
            id=openai_settings.embedder,
            dimensions=1024,
        )


openai_settings = OpenAISettings()


class DBSettings(BaseSettings):
    id: str = Field("agentos-db", description="id")
    driver: str = Field("postgresql+psycopg", description="driver")
    host: str = Field(..., description="host")
    port: int = Field(..., description="port")
    user: str = Field("postgres", description="user")
    password: str = Field(..., description="password")
    database: str = Field("ai", description="database")
    db_schema: str = Field("ai", description="ai", alias="DB_SCHEMA")

    model_config = SettingsConfigDict(env_prefix="DB_")

    @property
    def url(self):
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def create_postgres_db(self, contents_table: str | None = None) -> PostgresDb:
        """Create PostgresDb instance for the AgentOS.

        Pass contents_table when this database is used as the contents_db of a Knowledge base.
        For plain agent persistence (sessions, memory), leave it unset.
        """
        if contents_table is not None:
            return PostgresDb(
                id=self.id,
                db_url=self.url,
                db_schema=self.db_schema,
                knowledge_table=contents_table,
            )
        return PostgresDb(id=self.id, db_url=self.url, db_schema=self.db_schema)


db_settings = DBSettings()


def create_knowledge(name: str, table_name: str) -> Knowledge:
    """Creates a PgVector knowledge base with hybrid search."""
    return Knowledge(
        name=name,
        vector_db=PgVector(
            db_url=db_settings.url,
            schema=db_settings.db_schema,
            table_name=table_name,
            search_type=SearchType.hybrid,
            embedder=openai_settings.create_embedder(),
        ),
        contents_db=db_settings.create_postgres_db(
            contents_table=f"{table_name}_contents"
        ),
    )
