"""Test all imports exactly as Render does - run this before every push"""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

modules = [
    'from database.mongodb import check_connection, DATABASE_NAME',
    'from routes import auth',
    'from routes import users',
    'from routes import credit',
    'from routes import loans',
    'from routes import applications',
    'from routes import predictions',
    'from routes import recommendations',
    'from routes import active_loans',
    'from routes import payments',
    'from routes import admin',
    'from routes import dashboard',
    'from routes import notifications',
    'from routes import documents',
    'from routes import feedback',
    'from routes import datasets',
    'from routes import reports',
    'from routes import assessment',
]

failed = False
for stmt in modules:
    try:
        exec(stmt)
        print('OK  ' + stmt)
    except Exception as e:
        print('ERR ' + stmt)
        traceback.print_exc()
        failed = True
        break

if not failed:
    print('')
    print('ALL IMPORTS CLEAN - app will start on Render')
    sys.exit(0)
else:
    sys.exit(1)
