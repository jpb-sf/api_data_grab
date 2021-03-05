f"""Flask config."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Development:
	# """Set Flask config variables."""

	FLASK_ENV = 'development'
	TESTING = True
	SECRET_KEY = environ.get('SECRET_KEY')
	STATIC_FOLDER = 'static'
	TEMPLATES_FOLDER = 'templates'

	# Youtube API
	API_KEY = environ.get('API_KEY')

	# Directories
	# __file__ dunder is path of this module up to parent directory
	ROOT = path.dirname(__file__) + '/'
	UPLOAD = 'csv/'


class Production:
	# """Set Flask config variables."""

	FLASK_ENV = 'production'
	TESTING = False
	SECRET_KEY = environ.get('SECRET_KEY')
	STATIC_FOLDER = 'static'
	TEMPLATES_FOLDER = 'templates'

	# Youtube API
	API_KEY = environ.get('API_KEY')

	# Directories
	# __file__ dunder is path of this module up to parent directory
	ROOT = path.dirname(__file__) + '/'
	UPLOAD = 'csv/'


