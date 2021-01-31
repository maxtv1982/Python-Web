import asyncio
import aiosmtplib
import sqlalchemy as sa
import sys

from email.message import EmailMessage
from aiopg.sa import create_engine


if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
metadata = sa.MetaData()

user = sa.Table('user', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('username', sa.String(64), index=True, unique=True),
                sa.Column('email', sa.String(120), index=True, unique=True),
                sa.Column('password', sa.String(128)))


async def info_db():
    info = {}
    async with create_engine(user='postgres', database='flask_home', host='127.0.0.1', password='DB_PASS') as engine:
        async with engine.acquire() as conn:
            async for row in conn.execute(user.select()):
                info[row.username] = row.email
    return info


async def sender():
    for name, email in (await info_db()).items():
        message = EmailMessage()
        message["From"] = "test@mail.ru"
        message["To"] = email
        message["Subject"] = 'Asyncio'
        message.set_content("Уважаемый {}! Спасибо, что пользуетесь нашим сервисом объявлений".format(name))

        await aiosmtplib.send(message, hostname="smtp.mail.ru", port=465, username="USER", password="PASS",
                              use_tls=True)


loop = asyncio.get_event_loop()
loop.run_until_complete(sender())
