import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '853874302233-7b94g91bb02bs3nm831k22jf9q1gnbno.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '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')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
