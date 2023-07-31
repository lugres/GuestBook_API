from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from pydantic import BaseModel, EmailStr, SecretStr, ValidationError
from psycopg2.errors import UniqueViolation
from db import Database
from dependencies import get_db
from utils import get_psw_hash, prep_and_send

router = APIRouter(tags=['Accounts'])


class User(BaseModel):
    # in case there're more pydantic schemas, they're put into a separate schemas/models file
    email: EmailStr
    password: SecretStr


# @router.post('/update')
# def update(id: str, db: Database = Depends(get_db)):
#     result = db.update('users', ['active'], ['false'], where={'id': id})

#     return {'result': result}


@router.get('/activate')
def activate(token: str, db: Database = Depends(get_db)):
    # look for the token in the DB
    # does the token belong to the user?
    # if yes, and account is inactive, than activate it
    token_db = db.get_one(table='tokens', columns=[
        'token', 'user_id'], where={'token': token})

    if token_db:
        user_active = db.get_one(table='users', columns=['active'], where={
            'id': token_db.get('user_id')})
        if not user_active.get('active'):
            # we could have passed 'now()' - a DB function, so we would stick to DB timestamps
            # dt = datetime.now()
            result = db.update('users', ['active', 'activated_at'], [
                'true', 'now()'], where={'id': token_db.get('user_id')})
            return {'Activated users': result}
            # return {'message': 'Token is found!', 'result': token}
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='This user has been already activated!')
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Invalid token!')


@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(email: str, password: SecretStr = Query(default=None, min_length=8, max_length=16), db: Database = Depends(get_db), req: Request = None):
    '''Registring a user for our guestbook (with storing email and psw in DB)'''

    try:
        user = User(email=email, password=password)
        hashed_password = get_psw_hash(password.get_secret_value())

        # store hashed psw in DB
        # with db.conn:
        #     db.cursor.execute(
        #         'INSERT INTO users (email, password) VALUES (%s, %s);', (
        #             user.email, hashed_password)
        #     )

        user_id = db.write(table='users', columns=['email', 'password'], values=[
            user.email, hashed_password])

        user_token = str(uuid4())
        db.write(table='tokens', columns=['token', 'user_id'], values=[
            user_token, user_id])

        activation_url = f"{req.base_url}activate?token={user_token}"

        prep_and_send(user.email, activation_url)

        return {'status': 'You have successfully registered! Please activate your account by clicking on the link sent to your email.'}
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Email is not valid!')
        # return {'error': 'Email is not valid!'}
    except UniqueViolation:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail='A user by this email is already registered!')
        # return {'error': 'A user by this email is already registered!'}
