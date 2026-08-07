from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(15), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="User"
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Approved"
    )
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    bookings = db.relationship(
        "Booking",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

    def __repr__(self):
        return f"<User {self.name}>"