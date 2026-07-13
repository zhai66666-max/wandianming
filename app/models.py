from app import db
from app.beijing_time import beijing_now, beijing_today


class Person(db.Model):
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    student_id = db.Column(db.String(32), default='', index=True)
    department = db.Column(db.String(128), default='')
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=beijing_now)

    checkins = db.relationship('Checkin', backref='person', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'student_id': self.student_id,
            'department': self.department,
            'is_active': self.is_active,
        }

    def checked_in_today(self):
        """检查今天是否已签到"""
        return self.checkins.filter_by(check_date=beijing_today()).first() is not None


class Checkin(db.Model):
    __tablename__ = 'checkins'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, index=True)
    check_date = db.Column(db.Date, nullable=False, default=beijing_today, index=True)
    checked_at = db.Column(db.DateTime, default=beijing_now)

    __table_args__ = (
        db.UniqueConstraint('person_id', 'check_date', name='uq_person_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'name': self.person.name if self.person else '',
            'student_id': self.person.student_id if self.person else '',
            'check_date': self.check_date.isoformat(),
            'checked_at': self.checked_at.isoformat() if self.checked_at else '',
        }
