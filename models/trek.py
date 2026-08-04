from . import db


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)

    trek_name = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    difficulty = db.Column(
        db.String(50),
        nullable=False,
        default="Moderate"
    )

    slots = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Open"
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    description = db.Column(
        db.Text
    )

    bookings = db.relationship(
        "Booking",
        backref="trek",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Trek {self.trek_name}>"