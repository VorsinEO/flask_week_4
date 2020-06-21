import os
import random
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSON


app = Flask(__name__)
app.secret_key = "randomstring"
# - URL доступа к БД берем из переменной окружения DATABASE_URL
# до этого делай export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Создаем подключение к БД
db = SQLAlchemy(app)
# Создаем объект поддержки миграций
migrate = Migrate(app, db)

#Модель для хранения связей преподов и целей
teachers_goals_association = db.Table('teachers_goals', \
db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id')), \
db.Column('goal_id', db.Integer, db.ForeignKey('goals.id')))

#Модель для хранение преподователей
class Teacher(db.Model):
    #Таблица
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    about = db.Column(db.Text(), unique=True, nullable=False)
    rating = db.Column(db.Float)
    picture = db.Column(db.String(100), unique=True)
    price = db.Column(db.Integer, nullable=False)
    goals = db.relationship("Goal", secondary=teachers_goals_association)
    free = db.Column(JSON)

#Модель для хранения целей
class Goal(db.Model):
    #Таблица
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(100), unique=True, nullable=False)
    teachers = db.relationship("Teacher", secondary=teachers_goals_association)

#Модель для хранения бронирования
class Booking(db.Model):
    #Таблица
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)
    time_str = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    teacher = db.relationship("Teacher")
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))

#Модель для хранения запросов
class Request(db.Model):
    #Таблица
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    time_for_study = db.Column(db.String(200), nullable=False)
    goal = db.relationship("Goal")
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"))

#Объявляем WTF формы для бронирования препода и запроса на подбор препода
class BookingForm(FlaskForm):
    name = StringField('Имя пользователя', [InputRequired(), \
        Length(min=2, max=30, message="Введите от 2 до 30 символов")])
    phone = TelField('Телефон пользователя', [InputRequired(),\
        Length(min=10, max=16, message="Введите от 10 до 16 символов")])
    hidden_day_of_week = HiddenField('День недели')
    hidden_time_str = HiddenField('Время')
    hidden_tutor_id = HiddenField('Преподаватель')

class RequestForm(FlaskForm):
    name = StringField('Имя пользователя', [InputRequired(), \
        Length(min=2, max=30, message="Введите от 2 до 30 символов")])
    phone = TelField('Телефон пользователя', [InputRequired(),\
        Length(min=10, max=16, message="Введите от 10 до 16 символов")])
    goal = RadioField('Какая цель занятий?', choices=[("travel", "Для путешествий"),\
     ("study", "Для школы"), ("work", "Для работы"), ("relocate", "Для переезда")],\
      default='travel')
    time = RadioField('Сколько времени есть?', choices=[\
    ("1-2 часа в неделю", "1-2 часа в неделю"), ("3-5 часов в неделю", "3-5 часов в неделю")\
    , ("5-7 часов в неделю", "5-7 часов в неделю"), ("7-10 часов в неделю", "7-10 часов в неделю")]\
    , default="1-2 часа в неделю")

# словарь для расшифровки дней недели
day_of_week_labels = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда', 'thu': 'Четверг',\
    'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье'}

#главная
@app.route('/')
def main():
    #возьмем список преподов
    teachers_list = db.session.query(Teacher.id).all()
    # генерируем 6 рандомных ид преподов
    six_id = random.sample(teachers_list, 6)
    # фильтруем список преподов по six_id
    teachers_list_filter = db.session.query(Teacher).filter(Teacher.id.in_(six_id))
    goals = db.session.query(Goal).all()

    output = render_template('index.html', teachers_list_filter=teachers_list_filter, goals=goals)
    return output

#цели
@app.route('/goals/<goal>/')
def get_goal(goal):
    goal = db.session.query(Goal).filter(Goal.key == goal).scalar()
    goal_label = goal.value
    user_ids = [t.id for  t in  goal.teachers]
    teachers = db.session.query(Teacher).filter(Teacher.id.in_(user_ids)).\
    order_by(Teacher.rating.desc())
    output = render_template('goal.html', goal_label=goal_label,\
     teachers_list_filter_sorted=teachers)
    return output

#профиля учителя
@app.route('/profiles/<int:teacher_id>/')
def get_tutor(teacher_id):
    teacher = db.session.query(Teacher).get_or_404(teacher_id)
    output = render_template('profile.html', teacher=teacher, dow=day_of_week_labels)
    return output

#заявки на подбор
@app.route('/request/', methods=["GET", "POST"])
def get_request():
    form = RequestForm()

    if form.validate_on_submit() and (request.method == "POST"):
        #нашел на Stack способ передачи данных после валидации и редиректа
        goal = db.session.query(Goal).filter(Goal.key == form.goal.data).scalar()
        new_request = Request(
            name=form.name.data,
            phone=form.phone.data,
            time_for_study=form.time.data,
            goal=goal)
        db.session.add(new_request)
        db.session.commit()
        output = render_template('request_done.html', new_request=new_request, goal=goal)
        return output

    output = render_template('request.html', form=form)
    return output

#формы бронирования
@app.route('/booking/<int:id_tutor>/<day_of_week>/<time>/', methods=["GET", "POST"])
def get_booking(id_tutor, day_of_week, time):
    teacher = db.session.query(Teacher).get_or_404(id_tutor)
    dow_label = day_of_week_labels[day_of_week]
    #возвращаем исходный вид строке времени, в ссылке приходит первые два символа времени
    #и с  8 часами приходится разбираться
    if time[1] == ':':
        time_str = time + '00'
    else:
        time_str = time + ':00'
    form = BookingForm(hidden_day_of_week=day_of_week, hidden_time_str=time_str,\
     hidden_tutor_id=id_tutor)

    if form.validate_on_submit() and (request.method == "POST"):
        dow_label = day_of_week_labels[form.hidden_day_of_week.data]

        new_booking = Booking(
            day_of_week=form.hidden_day_of_week.data,
            time_str=form.hidden_time_str.data,
            name=form.name.data,
            phone=form.phone.data,
            teacher=teacher)

        db.session.add(new_booking)
        db.session.commit()
        output = render_template('booking_done.html', new_booking=new_booking, dow_label=dow_label)
        return output

    output = render_template('booking.html', teacher=teacher, day_of_week=day_of_week,\
         dow_label=dow_label, time_str=time_str, form=form)
    return output

if __name__ == '__main__':
    app.run()
