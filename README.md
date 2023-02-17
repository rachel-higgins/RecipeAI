# RecipeAI
1. Install virtualenv:
$ pip install virtualenv
2. Open a terminal in the project root directory and run:
$ virtualenv env
3. Then run the command:
$ source env/bin/activate
4. Then install the dependencies:
$ (env) pip install -r requirements.txt
5. Then run the following commands:
$ >>> from app import app, db
$ >>> app.app_context().push()
$ >>> db.create_all()
$ >>> exit()
5. Finally start the web server:
$ (env) python app.py
