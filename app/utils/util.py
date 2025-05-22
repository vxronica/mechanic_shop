from datetime import datetime, timedelta, timezone
from jose import jwt
import jose
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "a super secret, secret key"

def encode_token(user_id): #using unique pieces of info to make our tokens user specific
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0,hours=1), #Setting the expiration time to an hour past now
        'iat': datetime.now(timezone.utc), #Issued at
        'sub':  str(user_id) #This needs to be a string or the token will be malformed and won't be able to be decoded.
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Look for the token in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
            if not token:
                return jsonify({'message': 'Token is missing!'}), 400

            try:
                # Decode the token
                data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user_id = data['sub']  # Fetch the user ID
                
            except jose.exceptions.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired!'}), 400
            except jose.exceptions.JWTError:
                return jsonify({'message': 'Invalid token!'}), 400

            #return f(user_id, *args, **kwargs)
            return f(*args, user_id=user_id, **kwargs)
        else: 
            return jsonify({'message': 'You must be logged in to access this!'}), 400

    return decorated