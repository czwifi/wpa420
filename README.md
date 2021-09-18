# wpa420

TODO: summary of what this is

## setup
1. Install all python requirements `pip3 install -r requirements.txt`
2. Set up a MySQL/MariaDB database
3. Edit .env file to match your settings
4. `python3 manage.py makemigrations wifi && python3 manage.py migrate && python3 manage.py collectstatic --no-input`
5. `python3 manage.py createsuperuser`
6. Set up a web server (for example gunicorn or you can temporarily use the built in one)
7. Set up celery (worker and beat) and Redis (note: worker URL is currently hardcoded)
8. Log into the admin interface (/admin) and create any additional standard accounts you might need. Also create a WifiUser for yourself and any of these users.
9. Potentially import any JSON backups you have at /uploadJson
