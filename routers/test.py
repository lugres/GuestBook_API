from fastapi import APIRouter, Form, Depends, HTTPException, status
from db import Database
from dependencies import get_db, validate_user

router = APIRouter(tags=['Testing'])


@router.get('/testing')
def get_messages_which_contain(num: int = 3, search_pattern: str = None, db: Database = Depends(get_db), user_id: int = Depends(validate_user)):

    # result_messages = db.get_contains(table='guestbook', columns=[
    #     'message'], search=search_pattern, limit=num)
    # result_messages = db.get(table='guestbook', columns=['message'], limit=num, where={
    #                          'user_id': user_id}, contains={'message': search_pattern})
    # result_messages = db.get(table='guestbook', columns=[
    #                          'message'], limit=num, contains={'message': search_pattern})
    result_messages = db.get(table='guestbook', columns=['message'], limit=num, where={
                             'user_id': user_id}, contains={'message': search_pattern})

    return result_messages
