from typing import Optional

from sqlalchemy.orm import Session

import models
import schemas
from keygen import create_random_key, create_unique_random_key


def create_db_url(
    db: Session, url: schemas.URLBase, key: Optional[str] = None
        ) -> models.URL:
    '''
    Creates a shortened URL for the long URL
    (if key for the shortened URL is not provided, generates a random key)
    and writes the result to a database.

    Parameters:
        db: Session
        url: schemas.URLBase
        key: Optional[str]

    Returns:
        models.URL
    '''
    if not key:
        key = create_unique_random_key(db)

    secret_key = f'{key}_{create_random_key(length=8)}'

    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
        )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def get_db_url_by_key(db: Session, url_key: str) -> Optional[models.URL]:
    '''
    Gets the database URL by a key.
    Returns None if the URL with the key does not exist in the database.

    Parameters:
        db: Session
        url_key: str

    Returns:
        Optional[models.URL]
    '''
    return db.query(models.URL).filter(
        models.URL.key == url_key, models.URL.is_active
        ).first()


def get_db_url_by_secret_key(
    db: Session, secret_key: str
        ) -> Optional[models.URL]:
    '''
    Gets the database URL by a secret key.
    Returns None if the URL with the secret key does not exist in the database.

    Parameters:
        db: Session
        secret_key: str

    Returns:
        Optional[models.URL]
    '''
    return db.query(models.URL).filter(
        models.URL.secret_key == secret_key, models.URL.is_active
        ).first()


def update_db_clicks(db: Session, db_url: schemas.URL) -> schemas.URL:
    '''
    Updates the URL clicks count in the database.

    Parameters:
        db: Session
        db_url: schemas.URL

    Returns:
        schemas.URL
    '''
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url


def deactivate_db_url_by_secret_key(
    db: Session, secret_key: str
        ) -> Optional[models.URL]:
    '''
    Deactivates a database URL by a secret key.
    Returns None if the URL with the secret key does not exist in the database.

    Parameters:
        db: Session
        secret_key: str

    Returns:
        Optional[models.URL]
    '''
    db_url = get_db_url_by_secret_key(db, secret_key)

    if db_url:
        db_url.is_active = False  # type: ignore
        db.commit()
        db.refresh(db_url)

    return db_url
