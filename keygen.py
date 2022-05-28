from secrets import choice
from string import ascii_uppercase, digits

from sqlalchemy.orm import Session

import crud


def create_random_key(length: int = 5) -> str:
    '''
    Creates a random key of a given length from uppercase letters and digits.

    Parameters:
        length: int = 5

    Returns:
        str
    '''
    return ''.join(choice(ascii_uppercase + digits) for _ in range(length))


def create_unique_random_key(db: Session, length: int = 5) -> str:
    '''
    Creates a random key of a given length
    which does not already exists in a database.

    Parameters:
        db: Session
        length: int = 5

    Returns:
        str
    '''
    key = create_random_key(length=length)

    while crud.get_db_url_by_key(db, key):
        key = create_random_key(length=length)

    return key
