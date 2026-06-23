# BFG database

commands: 
venv\Scripts\activate
cd djangoProject
python manage.py makemigrations managementApp
python manage.py runserver

docker exec BFG-backend python manage.py seed