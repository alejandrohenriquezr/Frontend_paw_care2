import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '853874302233-7b94g91bb02bs3nm831k22jf9q1gnbno.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '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')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType

Transaction.commerce_code = '597055555532'
# api_key que aparece en la web de transbank es:
# 579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C
#Transaction.api_key = '123456789ABCDEF123456789ABCDEF123456789A'  # api_key de integración
Transaction.api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'  # api_key de integración

Transaction.integration_type = IntegrationType.TEST  # TEST para pruebas