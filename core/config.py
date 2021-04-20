import os


class Config:
	# Client config
	DEF_PREFIX = 'p.'
	OWNERS = (660110922865704980,)
	MIN_BALANCE = -5000
	TEMP_PATH = '././data/tempfiles/'
	IMAGES_PATH = '././data/images/'
	FONT = './data/fonts/a_AlternaSw.ttf'
	SAVE_IMG = './data/images/usercard.png'
	HELP_SERVER = 'https://discord.gg/6SHKgj43r9'
	FOOTER_TEXT = 'ProstoTools.exe || Copyright 2020-2021'
	MUTE_ROLE = 'PT-MUTED'
	VMUTE_ROLE = 'PT-VMUTED'
	SOFTBAN_ROLE = 'PT-SOFT-BANNED'
	CAPTCHA_ROLE = "PT-CHECKING"
	COLOR_ROLE = 'PT-COLOR-'
	LOW_LEVEL_API_KEY = os.getenv('BOT_API_KEY', default='somesuperduperapikey')
	TOKEN = os.getenv('BOT_TOKEN')
	DEFAULT_PREFIX = "p."
	MESSAGE_FILTERS = (
		"--with-attachments",
		"--without-attachments",
		"--with-embeds",
		"--without-embeds",
		"--with-reactions",
		"--without-reactions",
		"--with-mentions",
		"--without-mentions",
		# "--with-emojis",
		# "--without-emojis"
	)
	MEMBERS_FILTERS = (
		"--has-roles",
		"--hasnt--roles",
		"--bot",
		"--not-bot",
		"--online",
		"--offline"
	)
	FILTERS = (*MEMBERS_FILTERS, *MESSAGE_FILTERS)
	MESSAGES_FILTERS_PREDICATES = {
		"--with-attachments": lambda m: len(m.attachments) > 0,
		"--without-attachments": lambda m: len(m.attachments) <= 0,
		"--with-embeds": lambda m: len(m.embeds) > 0,
		"--without-embeds": lambda m: len(m.embeds) <= 0,
		"--with-reactions": lambda m: len(m.reactions) > 0,
		"--without-reactions": lambda m: len(m.reactions) <= 0,
		"--with-mentions": lambda m: len(m.mentions) > 0,
		"--without-mentions": lambda m: len(m.mentions) <= 0,
		# "--with-emojis": lambda m: m,
		# "--without-emojis": lambda m: m,
		"--has-roles": lambda m: len(m.author.roles) > 0,
		"--hasnt-roles": lambda m: len(m.author.roles) <= 0,
		"--bot": lambda m: m.author.bot,
		"--not-bot": lambda m: not m.author.bot,
		"--online": lambda m: m.author.status in ("online", "idle", "dnd"),
		"--offline": lambda m: m.author.status not in ("online", "idle", "dnd"),
	}
	MEMBERS_FILTERS_PREDICATES = {
		"--has-roles": lambda m: len(m.roles) > 0,
		"--hasnt-roles": lambda m: len(m.roles) <= 0,
		"--bot": lambda m: m.bot,
		"--not-bot": lambda m: not m.bot,
		"--online": lambda m: m.status in ("online", "idle", "dnd"),
		"--offline": lambda m: m.status not in ("online", "idle", "dnd"),
	}
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
	EXTENSIONS = (
		"cogs.clans",
		"cogs.different",
		"cogs.economy.economy",
		"cogs.fun.other",
		"cogs.fun.edit_image",
		"cogs.fun.random_image",
		"cogs.moderate",
		"cogs.owner",
		"cogs.utils",
		"cogs.works",
		"cogs.show_configs",
		"cogs.giveaways",
		"cogs.information",
		"cogs.reminders",
		"cogs.status_reminders",
		"cogs.settings",
		"cogs.help",
		"tasks.message_stat",
		"tasks.other",
		"tasks.punishments",
		"tasks.server_stat",
		"tasks.send_data",
		"tasks.bot_stat",
		"tasks.giveaways",
		"events.error_handler",
		"events.custom_voice_channel",
		"events.join",
		"events.leave",
		"events.leveling",
		"events.audit",
		"events.auto_reactions",
		"events.custom_commands",
		"events.autoresponders",
		"events.anti_flud",
		"events.anti_invite",
		"events.captcha",
		"events.anti_caps",
		"events.status_reminders",
		"events.anti_mentions",
		"events.auto_nick_corrector"
	)

	# Database config
	DB_PASSWORD = os.getenv('DB_PASSWORD')
	DB_HOST = os.getenv('DB_HOST')
	DB_USER = os.getenv('DB_USER')
	DB_DATABASE = os.getenv('DB_DATABASE')
