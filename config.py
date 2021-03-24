import os


class Config:
	# Client config
	DEF_PREFIX = 'p.'
	OWNERS = (660110922865704980,)
	SHOPLIST_COSTS = [500, 1000, 100, 1100, 100, 600]
	MIN_BALANCE = -5000
	TEMP_PATH = './data/tempfiles/'
	IMAGES_PATH = './data/images/'
	FONT = './data/fonts/a_AlternaSw.ttf'
	SAVE_IMG = './data/images/usercard.png'
	BOT_NAME = 'ProstoTools.exe'
	BOT_ID = 700767394154414142
	HELP_SERVER = 'https://discord.gg/6SHKgj43r9'
	FOOTER_TEXT = 'ProstoTools.exe || Copyright 2020-2021'
	MUTE_ROLE = 'PT-MUTED'
	VMUTE_ROLE = 'PT-VMUTED'
	SOFTBAN_ROLE = 'PT-SOFT-BANNED'
	CAPTCHA_ROLE = "PT-CHECKING"
	COLOR_ROLE = 'PT-COLOR-'
	TOKEN = os.getenv('BOT_TOKEN')
	ALLOWED_COGS = (
		"Clans",
		"Different",
		"Economy",
		"Games",
		"Moderate",
		"Settings",
		"Utils",
		"Reminders",
		"StatusReminders",
		"Works",
		"FunOther",
		"FunEditImage",
		"FunRandomImage",
		"Information"
	)
	PERMISSIONS_DICT = {
		"add_reactions": "Добавлять реакции",
		"administrator": "Администратора",
		"attach_files": "Прикреплять вложения",
		"ban_members": "Банить участников",
		"change_nickname": "Изменять никнеймы",
		"connect": "Подключатся к голосовому каналу",
		"create_instant_invite": "Создавать приглашения",
		"deafen_members": "Отключать в участников звук",
		"embed_links": "Отправлять эмбеды",
		"external_emojis": "Использовать внешнии эмодзи",
		"kick_members": "Кикать участников",
		"manage_channels": "Управлять каналами",
		"manage_emojis": "Управлять эмодзи",
		"manage_guild": "Управлять сервером",
		"manage_messages": "Управлять сообщениями",
		"manage_nicknames": "Управлять никнеймами",
		"manage_permissions": "Управлять разрешениями",
		"manage_roles": "Управлять ролями",
		"manage_webhooks": "Управлять вебхуками",
		"mention_everyone": "Упоминать @everyone",
		"move_members": "Перемещать участников",
		"mute_members": "Выключать микрофон в участников",
		"priority_speaker": "Приоритетный голос",
		"read_message_history": "Читать историю сообщений",
		"read_messages": "Читать сообщения",
		"send_messages": "Отправлять сообщения",
		"send_tts_messages": "Отправлять tts сообщения",
		"speak": "Говорить",
		"stream": "Стримить",
		"use_external_emojis": "Использовать внешнии эмодзи",
		"use_slash_commands": "Использовать слэш-команды",
		"use_voice_activation": "Использовать голосовую активацию",
		"view_audit_log": "Смотреть логи аудита",
		"view_channel": "Смотреть каналы",
		"view_guild_insights": "Смотреть статистику сервера",
	}

	# Database config
	DB_PASSWORD = os.getenv('DB_PASSWORD')
	DB_HOST = os.getenv('DB_HOST')
	DB_USER = os.getenv('DB_USER')
	DB_DATABASE = os.getenv('DB_DATABASE')
