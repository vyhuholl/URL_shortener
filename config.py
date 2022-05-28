from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    env_name: str = 'Local'
    base_url: str = 'http://localhost:8000'
    db: str = 'postgresql+psycopg2://postgres:@localhost:5432/url_shortener'

    class Config:
        env_file = '.env'


@lru_cache
def get_settings() -> Settings:
    '''
    Gets settings from the environment.

    Parameters:
        None

    Returns:
        Settings
    '''
    settings = Settings()
    print(f'Loading settings for: {settings.env_name}')
    return settings
