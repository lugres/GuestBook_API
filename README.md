# GuestBook_API
GuestBook API study project (fastapi, PostgreSQL)

GuestbookAPI app with PostgreSQL and FastAPI, deployed on Deta cloud; with a generic OOP DB helper with psycopg2 to generate dynamic SQL from Python code, no ORM was used.


Project requirements:
 - a web-based API serving json and using postgres as persistance layer;
 - supports user regisration and authentication using HTTP Basic Auth;
 - queries are dynamically generated at runtime using a custom-defined Database type;
 - users are able to post messages, update and delete them, vote on user public messages, etc.
