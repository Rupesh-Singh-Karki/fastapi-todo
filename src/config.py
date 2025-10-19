from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    db_uri: str = Field(..., env="DB_URI")
    root_path: str = Field("", env="ROOT_PATH")
    logging_level: str = Field("INFO", env="LOGGING_LEVEL")
    mongo_db: str = Field(..., env="MONGO_DB")
    todo_collection: str = Field(...,env="TODO_COLLECTION")
    user_collection: str = Field(...,env="USER_COLLECTION")
    jwt_secret_key: str = Field(...,env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(30,env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    #email
    email_sender: str = Field(..., env="EMAIL_SENDER")
    email_password: str = Field(..., env="EMAIL_PASSWORD")
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    email_enabled: bool = Field(True, env="EMAIL_ENABLED")
    #redis
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")


settings = Settings()