from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address) #creating and instance of Limiter
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})