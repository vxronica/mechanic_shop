from app import create_app
from app.models import db

#app = create_app('DevelopmentConfig')
app = create_app('development')
with app.app_context():
    #db.drop_all()
    db.create_all()

app.run()#debug=True to run