from .database import Database
from sanic import response, Blueprint

bp = Blueprint("api", url_prefix="/api")


@bp.get("/users")
async def users(request):
	return response.json(await Database().get_users())


@bp.get("/users/<guild_id:int>/<user_id:int>")
async def get_user(request, guild_id: int, user_id: int):
	return response.json(await Database().get_user(guild_id=guild_id, user_id=user_id))


@bp.get("/users/<user_id:int>/bio")
async def get_user_bio(request, user_id: int):
	return response.json(await Database().get_user_bio(user_id))


@bp.get("/users/<guild_id:int>/<user_id:int>/warns")
async def get_user_warns(request, guild_id: int, user_id: int):
	return response.json(
		await Database().get_user_warns(user_id=user_id, guild_id=guild_id)
	)


@bp.get("/users/<guild_id:int>/<user_id:int>/punishments")
async def get_user_punishments(request, guild_id: int, user_id: int):
	return response.json(
		await Database().get_user_punishments(guild_id=guild_id, user_id=user_id)
	)


@bp.get("/users/<guild_id:int>/<user_id:int>/reminders")
async def get_user_reminders(request):
	return response.json(await Database().get_user_reminders())
