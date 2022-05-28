from typing import Dict, Generator, Optional

import requests
import validators  # type: ignore
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from requests.exceptions import ConnectionError
from sqlalchemy.orm import Session
from starlette.datastructures import URL

import crud
import models
import schemas
from config import get_settings
from database import SessionLocal, engine

app = FastAPI()
models.Base.metadata.create_all(bind=engine)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[SessionLocal, None, None]:  # type: ignore
    '''
    Gets the database.

    Parameters:
        None

    Returns:
        Generator[SessionLocal, None, None]
    '''
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message: str) -> None:
    '''
    Raises an exception with the status code 400 and the given message.

    Parameters:
        message: str

    Returns:
        None
    '''
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(url: str) -> None:
    '''
    Raises an exception "URL does not exists" for a given URL.

    Parameters:
        url: str

    Returns:
        None
    '''
    raise HTTPException(status_code=404, detail=f"URL '{url}' doesn't exist")


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    '''
    Gets administration info for the URL.

    Parameters:
        db_url: models.URL

    Returns:
        schemas.URLInfo
    '''
    base_url = URL(get_settings().base_url)

    admin_endpoint = app.url_path_for(
        'administration info', secret_key=db_url.secret_key
        )

    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


@app.get('/')
async def read_root() -> str:
    '''
    Returns the welcome message.

    Parameters:
        None

    Returns:
        str
    '''
    return 'Welcome to the URL shortener API :)'


@app.post('/url', response_model=schemas.URLInfo)
async def create_url(
    url: schemas.URLBase,
    key: Optional[str] = None,
    db: Session = Depends(get_db)
        ) -> schemas.URLInfo:
    '''
    Creates a shortened URL (optionally – by a given key)
    and writes it to the database.
    Raises HTTP 400 Bad Request exception
    if the long URL is not valid or
    an URL with a given key already exists in the database.
    Raises HTTP 404 Not Found exception
    if the long URL points to a non-existing website.

    Parameters:
        url: schemas.URLBase
        key: Optional[str]
        db: Session

    Returns:
        schemas.URLInfo
    '''
    if not validators.url(url.target_url):
        raise_bad_request('Your provided URL is not valid')

    if key and crud.get_db_url_by_key(db, key):
        raise_bad_request('Key already exists in the database.')

    try:
        requests.get(url.target_url)
    except ConnectionError:
        raise_not_found(url.target_url)

    db_url = crud.create_db_url(db=db, url=url, key=key)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key
    return db_url


@app.get('/{key}')
async def forward_to_target_url(
    key: str, request: Request, db: Session = Depends(get_db)
        ) -> RedirectResponse:
    '''
    Forwards the URL key to the target URL.
    Raises HTTP 404 Not Found exception
    if the URL with the given key does not exists in the database.

    Parameters:
        key: str
        request: Request
        db: Session

    Returns:
        RedirectResponse
    '''
    if db_url := crud.get_db_url_by_key(db=db, url_key=key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(f'{get_settings().base_url}/{key}')


@app.get('/peek/{key}')
async def peek_target_url(
    key: str, request: Request, db: Session = Depends(get_db)
        ) -> Optional[Dict[str, str]]:
    '''
    Returns the target URL by URL key
    Raises HTTP 404 Not Found exception
    if the URL with the given key does not exists in the database.

    Parameters:
        key: str
        request: Request
        db: Session

    Returns:
        Optional[Dict[str, str]]
    '''
    if db_url := crud.get_db_url_by_key(db=db, url_key=key):
        return {'target_url': db_url.target_url}
    else:
        raise_not_found(f'{get_settings().base_url}/{key}')

    return None


@app.get(
    '/admin/{secret_key}',
    name='administration info',
    response_model=schemas.URLInfo
        )
async def get_url_info(
    secret_key: str, request: Request, db: Session = Depends(get_db)
        ) -> Optional[schemas.URLInfo]:
    '''
    Gets URL info by a secret key.
    Raises HTTP 404 Not Found exception
    if the URL with the given key does not exists in the database.

    Parameters:
        secret_key: str
        request: Request
        db: Session

    Returns:
        Optional[schemas.URLInfo]
    '''
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found('')

    return None


@app.delete('/admin/{secret_key}')
async def delete_url(
    secret_key: str, request: Request, db: Session = Depends(get_db)
        ) -> Optional[Dict[str, str]]:
    '''
    Deletes URL from a database by a secret key.
    Raises HTTP 404 Not Found exception
    if the URL with the given key does not exists in the database.

    Parameters:
        secret_key: str
        request: Request
        db: Session

    Returns:
        Optional[Dict[str, str]]
    '''
    if db_url := crud.deactivate_db_url_by_secret_key(
        db, secret_key=secret_key
            ):
        message = f'Successfully deleted shortened URL for {db_url.target_url}'
        return {'detail': message}
    else:
        raise_not_found('')

    return None
