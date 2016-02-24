# NOSS

A group of apis to suggest as well as plan your journey depending on our rich database and rating criteria.
All the apis hosted on https://dry-mountain-9680.herokuapp.com/ and documentation on http://dry-mountain-9680.herokuapp.com/docs/ . 

To install locally follow these steps.

1. git clone https://github.com/nitingera1996/NOSS.git

2. Make sure you have python and virtual env installed.

3. Make a virtual env by virtualenv venv.

4. Activate it by, source venv/bin/activate

5. Install all the requirements by pip install -r requirements.txt

6. Create the database by python manage.py syncdb

7. Populate ur database with python populate_cities.py

8. Run python manage.py createcachetable

9. Then run the server with python manage.py runserver
