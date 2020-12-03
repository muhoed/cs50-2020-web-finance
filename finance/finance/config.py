from tempfile import mkdtemp

# set assets folders
STATIC_FOLDER = "static"
TEMPLATES_FOLDER = "template"

# Ensure templates are auto-reloaded
TEMPLATES_AUTO_RELOAD = True

# Configure session to use filesystem (instead of signed cookies)
SESSION_FILE_DIR = mkdtemp()
SESSION_PERMANENT = False
SESSION_TYPE = "filesystem"

# Database config
SQLALCHEMY_DATABASE_URI = "sqlite:///finance.db"
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

