from sqlalchemy import create_engine
from settings import settings   

import psycopg2
print(psycopg2.__version__)


DATABASE_URI = f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
print(DATABASE_URI) 
engine = create_engine(DATABASE_URI, connect_args={"options": f"-c search_path={settings.postgres_schema}"})