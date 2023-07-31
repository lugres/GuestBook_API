from fastapi import APIRouter, Form, Depends, HTTPException, status
from db import Database
from dependencies import get_db, validate_user

router = APIRouter(tags=['Messages'])


@router.get('/messages/most_upvoted')
def get_most_upvoted_messages(db: Database = Depends(get_db)):
    messages = db.get('top_messages', ['id', 'message', 'n_upvotes'])
    return messages


@router.post('/messages/{message_id}/upvote')
def upvote_a_message(message_id: int, db: Database = Depends(get_db), user_id: int = Depends(validate_user)):
    # try to get the message
    # if doesn't exist, raise HTTP exc
    # if it does exists, but it's owned by this user, is a private one, or it was already upvoted, raise HTTP exc
    # otherwise upvote the message
    message_db = db.get_one(
        'guestbook', ['id', 'user_id', 'private'], where={'id': message_id})

    if not message_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='A message by this ID was not found.')

    if message_db.get('user_id') == user_id or message_db.get('private'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You can not upvote your own or private messages!')

    already_upvoted = db.get_one(
        'upvotes', ['id'], where={'message_id': message_id, 'user_id': user_id})

    if already_upvoted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You can not upvote the same message more than once!')

    upvoted_message = db.write(table='upvotes', columns=['user_id', 'message_id'], values=[
        user_id, message_id])

    return {'Result': 'A message was successfully upvoted, thank you!', 'message_id': message_id}


@router.post('/messages')
def write_a_message_on_the_guestbook(message: str = Form(...), private: bool = Form(False),
                                     db: Database = Depends(get_db), user_id: int = Depends(validate_user)):
    message_id = db.write(table='guestbook', columns=['message', 'user_id', 'private'], values=[
        message, user_id, private])

    return {'Result': 'A message record inserted into DB', 'message_id': message_id, 'message': message}


@router.patch('/messages/{message_id}')
def update_a_specific_message(message_id: int, message: str = Form(...), private: bool = Form(False),
                              db: Database = Depends(get_db),
                              user_id: str = Depends(validate_user)):
    # try to get the message
    # if it doesn't exist, raise HTTP Exc
    # if it does exists, but user_id doesn't own it, raise HTTP Exc
    # otherwise update the message

    message_db = db.get_one(
        'guestbook', ['id', 'user_id'], where={'id': message_id})

    if not message_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Message was not found.')

    if message_db.get('user_id') == user_id:
        result = db.update('guestbook', ['message', 'private'], [
                           message, private], where={'id': message_id})
        return {'Updated messages': result}

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail='You are not allowed to update this message!')


@router.get('/messages/search')
def search_for_messages_by_keyword(search_pattern: str, num: int = 10, db: Database = Depends(get_db), user_id: int = Depends(validate_user)):

    # This doesn't work as expected, as we get additional messages due to only one AND with a LIKE search pattern.
    # We could have refactored db.get so AND clause with search_pattern is present for both where and or_where.
    # One more option - re-write SQL query to re-order query containers, so first we have WHERE LIKE search pattern, then AND (where or_where conditions).
    # Alternatively, we could have created a DB function or view and just invoke it.
    found_messages = db.get(table='guestbook', columns=['id', 'message', 'created_at'],
                            limit=num, where={'private': False},
                            or_where={'private': True, 'user_id': user_id}, contains={'message': search_pattern})

    return found_messages

    # public_messages = db.get(table='guestbook', columns=['id', 'message', 'private', 'created_at'],
    #                          where={'private': False}, contains={'message': search_pattern})

    # private_messages = db.get(table='guestbook', columns=['id', 'message', 'private', 'created_at'],
    #                           where={'private': True, 'user_id': user_id}, contains={'message': search_pattern})

    # found_messages = public_messages + private_messages

    # return found_messages[:num]


@router.get('/messages/{message_id}')
def view_a_specific_message(message_id: int,
                            db: Database = Depends(get_db),
                            user_id: str = Depends(validate_user)):

    message_db = db.get_one(
        'guestbook', ['id', 'user_id', 'message', 'created_at', 'private'], where={'id': message_id})

    if not message_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Message was not found.')

    if message_db.get('private') and message_db.get('user_id') != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to view this message!')

    return {'id': message_db.get('id'), 'message': message_db.get('message'), 'created_at': message_db.get('created_at')}


@router.get('/messages')
def get_all_messages(num: int = 3, db: Database = Depends(get_db), user_id: int = Depends(validate_user)):

    # messages_all = db.get(table='guestbook', columns=[
    #                       'id', 'user_id', 'message', 'created_at', 'private'])

    # if not messages_all:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail='No messages were found.')

    # filtered_messages = [{'id': message.get('id'), 'message': message.get('message'), 'created_at': message.get(
    #     'created_at')} for message in messages_all if (not message.get('private') or message.get('user_id') == user_id)]

    # return filtered_messages[:num]

    # Alternative approach - getting all public messages, then private ones owned by the autheticated user, and returning them combined in a requested number
    # Negative ascpects: 1) getting data from DB 2 times 2) quering more data than we need to return to the user
    # So we need to refactor out .get method to squize in all of the criterias in one go
    # public_messages = db.get(table='guestbook', columns=[
    #                          'id', 'message', 'created_at'], where={'private': False})
    # private_messages_by_user = db.get(table='guestbook', columns=[
    #     'id', 'message', 'created_at'], where={'private': True, 'user_id': user_id})

    # total_messages = public_messages + private_messages_by_user

    # return total_messages[:num]

    # Using refactored .get method with an additional or_where conditions
    total_messages = db.get(table='guestbook', columns=['id', 'message', 'created_at'],
                            limit=num, where={'private': False},
                            or_where={'private': True, 'user_id': user_id})

    return total_messages


@router.delete('/messages/{message_id}')
def delete_a_specific_message(message_id: int, db: Database = Depends(get_db), user_id: int = Depends(validate_user)):

    result = db.delete('guestbook', {'id': message_id, 'user_id': user_id})

    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Message was not found or you do not have permission to delete it.')

    return {'Deleted messages': result}
