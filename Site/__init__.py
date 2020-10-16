# Imports
import mysql.connector
import asyncio_redis

from flask import Flask
from sanic import Sanic
from sanic_session import Session, RedisSessionInterface
from sanic_jinja2 import SanicJinja2


# Create a redis interface
class Redis:
	"""
	A simple wrapper class that allows you to share a connection
	pool across your application.

	"""
	pool = None

	async def get_redis_pool(self):
		if not self.pool:
			self.pool = await asyncio_redis.Pool.create(
				host='localhost', port=6379, poolsize=10
			)

		return self.pool


# Initialize objects
app = Sanic(__name__)
app.static('static', './static/css')
app.update_config('config.Config')
# app.update_config('config.Config')
redis = Redis()
session = Session(app, interface=RedisSessionInterface(redis.get_redis_pool))
jinja = SanicJinja2(app)


# Work with DB
conn = mysql.connector.connect(user='root', passwd='9fr8-PkM;M4+', host='localhost', db='data')
cursor = conn.cursor(buffered=True)
