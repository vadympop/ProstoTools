import os

class Config:
	# Flask config
	SECRET_KEY = os.environ.get('SECRET_KEY')
	DEBUG = False

	# Flask main config
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_DEFAULT_SENDER = MAIL_USERNAME

	# Db config
	DB_PASSWORD = os.environ.get('DB_PASSWORD') or '9fr8-PkM;M4+'
	HOST = os.environ.get('DB_HOST') or 'localhost'
	USER = os.environ.get('DB_USER') or 'root'
	DATABASE = os.environ.get('DB_DATABASE') or 'data'

	# Bot info, oAuth config