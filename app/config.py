import os
import getpass

class Config:
    DB_NAME = "user_management"
    DB_USER = "postgres"
    DB_PASSWORD = None
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    def __init__(self):
        # Pitaj za password samo ako nije setovan
        if not Config.DB_PASSWORD:
            Config.DB_PASSWORD = getpass.getpass("Enter PostgreSQL password: ")
    
    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"