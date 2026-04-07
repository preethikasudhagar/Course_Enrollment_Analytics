import py_compile
import os
import sys

# Change to backend directory
os.chdir('backend')

files_to_check = [
    'main.py',
    'database.py',
    'models/models.py',
    'routes/auth.py',
    'routes/courses.py',
    'routes/enrollments.py',
    'routes/analytics.py',
    'routes/notifications.py',
    'routes/users.py',
    'routes/search.py',
    'routes/settings.py',
    'routes/suggestions.py',
    'routes/activity.py',
    'routes/seat_expansion.py'
]

print("Checking syntax for backend files...")
for f in files_to_check:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f}")
    except Exception as e:
        print(f"ERROR in {f}: {e}")
