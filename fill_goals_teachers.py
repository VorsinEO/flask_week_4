#Запустить 1 раз после создания таблиц из первого запуска app
import json
from app import db, Teacher, Goal

#получить преподов из JSON из проекта недели 3
def get_teachers_list():
    with open('teachers.json', 'r') as f:
        contents = f.read()
    teachers_list = json.loads(contents)
    return teachers_list

#получить цели из JSON из проекта недели 3
def get_goals_list():
    with open('goals.json', 'r') as f:
        contents = f.read()
    goals_list = json.loads(contents)
    return goals_list

#Заполним таблицу целей
if  db.session.query(Goal).get(1):
    print('Вы пытаетесь выполнить инициирующую загрузку целей повторно, очистите таблицы чтобы ее выполнить')
else:
    goals_for_table = get_goals_list()
    for key, value in goals_for_table.items():
        goal_add = Goal(key=key, value=value)
        db.session.add(goal_add)
    db.session.commit()

if  db.session.query(Teacher).get(1):
    print('Вы пытаетесь выполнить инициирующую загрузку преподов повторно, очистите таблицы чтобы ее выполнить')
else:
#Заполним таблицу преподавателей
    teachers_for_table = get_teachers_list()
    for teacher in teachers_for_table:
        teacher_add = Teacher(
            id = teacher['id'],
            name = teacher['name'],
            about = teacher['about'],
            rating = teacher['rating'],
            picture = teacher['picture'],
            price = teacher['price'],
            #goals мы добавим отдельно ниже
            free = teacher['free']
        )
        db.session.add(teacher_add)
        for goal in teacher['goals']:
            goal_filter = db.session.query(Goal).filter(Goal.key == goal).scalar()
            teacher_add.goals.append(goal_filter)
    db.session.commit()