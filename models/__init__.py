# pyre-ignore [missing-import]
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .trek import Trek
from .booking import Booking