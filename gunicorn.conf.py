# Gunicorn configuration

# accesslog = "gunicorn_access.log"  # Gunicorn access logs
errorlog = "error.log"   # Gunicorn error logs
loglevel = "debug"                # Log level (debug, info, warning, etc.)
capture_output = True             # Capture stdout/stderr to Gunicorn's error log

def on_starting(server):

    print("Running one-time startup code")
    from run import app
    from app.models import db

    with app.app_context():

        # Create the database (doesn't overwrite existing tables etc.)
        db.create_all()

        # Run the first run setup to create base values etc.
        from app.first_run import firstrun
        firstrun(app)