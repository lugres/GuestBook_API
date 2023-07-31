from passlib.context import CryptContext
from os import environ as env
from fastapi import HTTPException, status
import smtplib

pwd_context = CryptContext(schemes=['bcrypt'])


def get_psw_hash(password):
    return pwd_context.hash(password)


def verify_psw(plain_psw, hashed_psw):
    return pwd_context.verify(plain_psw, hashed_psw)


def prep_and_send(email_to, activation_url):
    try:

        my_email = env.get("UKRNET_ADDR")
        email_message = f"From: {my_email}\nSubject:GuestBookAPI Account Activation\n\nPlease activate your account by going to this link: {activation_url}".encode(
            "utf8")

        with smtplib.SMTP_SSL("smtp.ukr.net", port=465) as connection:
            connection.login(my_email, env.get("UKRNET_APP_PWD"))
            connection.sendmail(from_addr=my_email,
                                to_addrs=email_to, msg=email_message)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unable to send email. Your activation URL is {activation_url}")
