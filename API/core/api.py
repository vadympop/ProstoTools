from .database import Database
from .utils import Utils
from sanic import response, Blueprint
from sanic.exceptions import NotFound

bp = Blueprint("api", url_prefix="/api")


@bp.middleware("request")
async def check_user_agent(request):
	if "user-agent" not in request.headers.keys():
		return response.json({"message": "Unauthorized"}, status=405)


@bp.get("/users")
async def users(request):
	if "token" not in request.headers.keys():
		return response.json({"message": "An invalid key was provided"}, status=401)

	if not await Utils().check_bot_token(token=request.headers["token"]):
		return response.json({"message": "An invalid key was provided"}, status=401)
	
	return response.json(await Database().get_users())


@bp.get("/users/<guild_id:int>/<user_id:int>")
async def get_user(request, guild_id: int, user_id: int):
	if "key" not in request.headers.keys():
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	if not await Utils().check_api_key(api_key=request.headers["key"], guild_id=guild_id):
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	return response.json(
		await Database().get_user(guild_id=guild_id, user_id=user_id), status=200
	)


@bp.get("/users/<guild_id:int>/<user_id:int>/warns")
async def get_user_warns(request, guild_id: int, user_id: int):
	if "key" not in request.headers.keys():
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	if not await Utils().check_api_key(api_key=request.headers["key"], guild_id=guild_id):
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	return response.json(
		await Database().get_user_warns(user_id=user_id, guild_id=guild_id), status=200
	)


@bp.get("/users/<guild_id:int>/<user_id:int>/punishments")
async def get_user_punishments(request, guild_id: int, user_id: int):
	if "key" not in request.headers.keys():
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	if not await Utils().check_api_key(api_key=request.headers["key"], guild_id=guild_id):
		return response.json({"message": "An invalid API-Key was provided"}, status=401)
		
	return response.json(
		await Database().get_user_punishments(guild_id=guild_id, user_id=user_id),
		status=200,
	)


@bp.get("/users/<guild_id:int>/<user_id:int>/reminders")
async def get_user_reminders(request, guild_id: int, user_id: int):
	if "key" not in request.headers.keys():
		return response.json({"message": "An invalid API-Key was provided"}, status=401)

	if not await Utils().check_api_key(api_key=request.headers["key"], guild_id=guild_id):
		return response.json({"message": "An invalid API-Key was provided"}, status=401)
		
	return response.json(
		await Database().get_user_reminders(guild_id=guild_id, user_id=user_id),
		status=200,
	)


@bp.exception(NotFound)
async def exception_404(request, exception):
	return response.json({"message": "An invalid url was provided"}, status=404)
