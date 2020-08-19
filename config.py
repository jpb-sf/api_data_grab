"""Flask config."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
	# """Set Flask config variables."""

	FLASK_ENV = 'development'
	TESTING = True
	SECRET_KEY = environ.get('SECRET_KEY')
	STATIC_FOLDER = 'static'
	TEMPLATES_FOLDER = 'templates'

	# Youtube API
	API_KEY = environ.get('API_KEY')

	# Directories
	ROOT = '/Users/jasonbergland/Documents/Projects/FrontDEV/DevProjects/YT_Data/'
	UPLOAD = 'csv/'