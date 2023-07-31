from fastapi import FastAPI, Form
from routers import accounts, messages, test


app = FastAPI(
    title='Guestbook API',
    version='0.1.0',
    description='All your suggestions are stored here for further analysis...',
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

app.include_router(accounts.router)
app.include_router(messages.router)
app.include_router(test.router)


# HTTP GET requests

# @app.get('/')
# def root():
#     # some logic
#     # return something
#     return {'message': 'nothing is here, try /hello'}
