from functools import partial
from hashlib import md5
from aiohttp import web
from aiopg.sa import create_engine
import sqlalchemy as sq
from sqlalchemy.sql.ddl import CreateTable
import sys
import asyncio
from datetime import datetime
import jwt
from aiohttp_jwt import JWTMiddleware

import config


if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

metadata = sq.MetaData()

users = sq.Table('users', metadata,
                 sq.Column('id', sq.Integer, autoincrement=True, primary_key=True, nullable=False),
                 sq.Column('username', sq.String, nullable=False, unique=True),
                 sq.Column('email', sq.String, nullable=False, unique=True),
                 sq.Column('password', sq.String, nullable=False, unique=True), )

posts = sq.Table('posts', metadata,
                 sq.Column('id', sq.Integer, autoincrement=True, primary_key=True, nullable=False),
                 sq.Column('title', sq.String, nullable=False),
                 sq.Column('content', sq.String, nullable=False),
                 sq.Column('created_at', sq.DateTime(), default=datetime.utcnow()),
                 sq.Column('user_id', sq.Integer, sq.ForeignKey('users.id')), )


async def create_table():
    async with create_engine(dsn=config.POSTGRE_DSN) as engine:
        async with engine.acquire() as conn:
            await conn.execute('CREATE TABLE IF NOT EXISTS users (id Integer PRIMARY KEY, username varchar(40) NOT '
                               'NULL UNIQUE, email varchar(40) NOT NULL UNIQUE, password varchar(40) NOT NULL UNIQUE)')
            await conn.execute('CREATE TABLE IF NOT EXISTS posts (id Integer PRIMARY KEY, title varchar(255) NOT '
                               'NULL, content varchar(255) NOT NULL, created_at date, user_id Integer,'
                               'CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES users (id))')
    engine.close()


class UserView(web.View):

    async def get(self):
        user_id = self.request.match_info['user_id']
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            query = users.select().where(users.c.id == user_id)
            result = await conn.execute(query)
            user_inf = await result.fetchone()
            if user_inf:
                return web.json_response({'id': user_inf[0], 'name': user_inf[1]})
        raise web.HTTPNotFound()

    async def post(self):
        post_data = await self.request.json()
        try:
            name = post_data['username']
            password = md5(post_data['password'].encode()).hexdigest()
            email = post_data['email']
        except KeyError:
            raise web.HTTPBadRequest
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            try:
                result = await conn.execute(users.insert().values(username=name, password=password, email=email))
                user_inf = await result.fetchone()
            except KeyError:
                raise web.HTTPBadRequest
            payload = {'user_id': user_inf[0]}
            jwt_token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
            return web.json_response({'user_id': user_inf[0], 'token': jwt_token})

    async def delete(self):
        user_id = self.request.match_info['user_id']
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            query = users.select().where(users.c.id == user_id)
            result = await conn.execute(query)
            user_inf = await result.fetchone()
            if user_inf:
                query = users.delete().where(users.c.id == user_id)
                await conn.execute(query)
                return web.HTTPOk()
        raise web.HTTPBadRequest


class PostView(web.View):

    async def get(self):
        post_id = self.request.match_info['post_id']
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            query = posts.select().where(posts.c.id == post_id)
            result = await conn.execute(query)
            post_inf = await result.fetchone()
            if post_inf:
                return web.json_response({'id': post_inf[0], 'title': post_inf[1]})
        raise web.HTTPNotFound()

    async def post(self):
        post_data = await self.request.json()
        token = self.request.headers.get('authorization')
        try:
            title = post_data['title']
            content = post_data['content']
            user_id = jwt.decode(token[7:], config.JWT_SECRET, algorithms=config.JWT_ALGORITHM)['user_id']
        except KeyError:
            raise web.HTTPBadRequest

        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            result = await conn.execute(posts.insert().values(title=title, content=content, user_id=user_id))
            post_inf = await result.fetchone()

            return web.json_response({'post_id': post_inf[0]})

    async def delete(self):
        post_id = self.request.match_info['post_id']
        token = self.request.headers.get('authorization')
        user_id = jwt.decode(token[7:], config.JWT_SECRET, algorithms=config.JWT_ALGORITHM)['user_id']
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            query = posts.select().where(posts.c.id == post_id).where(posts.c.user_id == user_id)
            result = await conn.execute(query)
            post_inf = await result.fetchone()
            if post_inf:
                query = posts.select().where(posts.c.id == post_id)
                await conn.execute(query)
                return web.HTTPOk()
        raise web.HTTPNotFound()

# вывод всех объявлений - почему-то выводит только первое - в чём причина?
class PostsView(web.View):

    async def get(self):
        engine = self.request.app['pg_engine']

        async with engine.acquire() as conn:
            query = posts.select()
            result = await conn.execute(query)
            info = await result.fetchall()
            for item in info:
                return web.json_response({'id': item[0], 'title': item[1]})
        raise web.HTTPNotFound()


# Зарегистрируем подключение к БД (используя АЛХИМИЮ):
async def register_connection_alchemy(app: web.Application):
    engine = await create_engine(dsn=config.POSTGRE_DSN, minsize=2, maxsize=10)
    app['pg_engine'] = engine
    yield
    engine.close()


# основная вьюха (создаём, регистрируем)
async def get_app():
    await create_table()
    app = web.Application(
        middlewares=[JWTMiddleware(config.JWT_SECRET, algorithms=config.JWT_ALGORITHM, whitelist=[r'/api/user/login'])])
    app.cleanup_ctx.append(partial(register_connection_alchemy))
    app.router.add_view('/api/user/{user_id:\d+}', UserView)
    app.router.add_view('/api/user/login', UserView)
    app.router.add_view('/api/post/{post_id:\d+}', PostView)
    app.router.add_view('/api/post/', PostView)
    app.router.add_view('/api/posts/', PostsView)
    return app


if __name__ == '__main__':
    app = get_app()
    web.run_app(app, host='127.0.0.1', port=8080)
