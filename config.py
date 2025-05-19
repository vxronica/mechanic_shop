class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mechanic_shop.db' 
    DEBUG = True

class TestingConfig:
    pass

class ProductionConfig:
    pass