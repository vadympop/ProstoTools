
# Imports
import mysql.connector
import asyncio_redis

from core.views import bp
from sanic import Sanic
from sanic_session import Session
from sanic_jinja2 import SanicJinja2

# Initialize objects
app = Sanic(__name__)
app.update_config('Site.config.Config')
app.static('/static', './static/css')
session = Session()
app.register_blueprint(bp)

# Run the app
if __name__ == "__main__":
	app.run(port=5000, debug=True)