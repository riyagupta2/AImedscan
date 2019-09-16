TIMEZONE = 'Europe/Paris'

# Secret key for generating tokens
SECRET_KEY = 'houdini'

# Admin credentials
ADMIN_CREDENTIALS = ('admin', 'pa$$word')

# Database choice
SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True

# Configuration of a Gmail account for sending mails
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'riyagupta6018@gmail.com'
MAIL_PASSWORD = 'Absolute@2010$#'
ADMINS = ['riyagupta6018@gmail.com']

# Number of times a password is hashed
BCRYPT_LOG_ROUNDS = 12

