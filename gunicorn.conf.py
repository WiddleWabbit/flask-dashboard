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