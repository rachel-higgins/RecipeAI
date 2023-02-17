'''This is a Python Flask web application that generates recipe suggestions using OpenAI's GPT-3 API. The user provides certain criteria, such as a protein option, a special ingredient, and a region, and the API generates a recipe based on the given inputs. The generated recipe is then stored in a SQLite database and displayed to the user. The user can also edit and delete the recipe entries.

The code includes the necessary imports, such as Flask, SQLAlchemy, requests, and json. It creates a Flask app object, configures the app's database, and initializes a SQLAlchemy database. The database schema is defined in the Todo class, which has id, options, name, content, and date_created attributes.

There are three routes in the code. The index route displays the list of previously generated recipes and a form to add a new recipe. If the user submits the form, the app sends a request to the OpenAI API to generate a recipe, and the API's response is used to create a new recipe entry in the database. The delete route allows the user to delete a recipe from the database, and the view route displays the details of a recipe and allows the user to edit the recipe content.'''

from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json

# Initialize with your personal OpenAI API key 
OPENAI_API_KEY = ''

# create app object
app = Flask(__name__)

# gives app database location
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # ///=relative path

# initialize database
with app.app_context():
    db = SQLAlchemy(app)


class Todo(db.Model):
    """Represents a recipe in the database.

    Attributes:
        id (int): The unique identifier for the recipe.
        options (str): A comma-separated list of recipe options.
        name (str): The name of the recipe.
        content (str): The recipe's ingredients and steps.
        date_created (datetime): The date and time the recipe was added.
    """
    # id column is an integer that refrences the id of each entry
    id = db.Column(db.Integer, primary_key=True)
    # options column stores the option details for the prompt
    options = db.Column(db.String(100), nullable=False)
    # name column stores a name for each entry
    name = db.Column(db.String(100), nullable=False, default="Anonymous")
    # content is a text column holds each task content details
    content = db.Column(db.String(600), nullable=False)
    # creates a timestamp for a new entry
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # returns a string everytime a new element is created
    def __repr__(self):
        return '<Task %r>' % self.id


@app.route('/', methods=['POST', 'GET'])
def index():
    """Displays a list of recipes and a form to add a new recipe.
    If a POST request is received, a new recipe is created and added to the database.

    Returns:
        If a GET request is received, the rendered HTML template is returned.
        If a POST request is received, the user is redirected to the homepage.
    """
    if request.method == 'POST':
        # get recipe options from the user
        protein_option = request.form['protein_option']
        special_ingredient = request.form['special_ingredient']
        region_one = request.form['region_one']
        region_two = request.form['region_two']
        recipe_options = f'{protein_option}, {special_ingredient}, {region_one}, {region_two}'

        # if region two is none the value should hold no strings
        if(region_two == 'None'):
            region_two = ''

        # get a name for the recipe, if name is blank a name is generated
        recipe_name = request.form['name']
        if(recipe_name == ''):
            recipe_name = f'{region_one}-{region_two} {special_ingredient} {protein_option}'

        # send request to OpenAI API
        prompt = openAI_prompt(protein_option, special_ingredient, region_one, region_two)
        headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {OPENAI_API_KEY}"}
        # json.dumps() converts request data to JSON str ensuring proper formatting and escape
        data = json.dumps({
            "model": "text-davinci-002",
            "prompt": prompt,
            "temperature": 0.5,
            "max_tokens": 600
        })
        response = requests.post('https://api.openai.com/v1/completions', headers=headers, data=data)

        # handle the returned API response
        if response.status_code != 200: # error response 
            abort(500, description='There was an issue generating your recipe')
        else:   # if no errors greate a new recipe w/ name, options, & content
            recipe_content = response.json()['choices'][0]['text']
            new_recipe = Todo(options=recipe_options, name=recipe_name, content=recipe_content)
            try:
                db.session.add(new_recipe)
                db.session.commit()
                return redirect('/')  # redirects to homepage
            except:
                abort(500, description='There was an issue creating your recipe')
    else:  # display previously generated recipes
        recipe = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=recipe)


@app.route('/delete/<int:id>')
def delete(id):
    """Delete a recipe from the database.

    Args:
        id (int): The ID of the recipe to delete.

    Returns:
        A redirect response to the homepage if the recipe is successfully deleted.
        An error page if there is a problem deleting the recipe.
    """
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return abort(500, description='There was a problem deleting your recipe')


@app.route('/view/<int:id>', methods=['GET', 'POST'])
def view(id):
    """Display the details of a recipe and allow editing.

    Args:
        id (int): The ID of the recipe to display.

    Returns:
        A view template that displays the recipe details and an editing form.
        A redirect response to the homepage if the recipe is successfully updated.
        An error page if there is a problem displaying or updating the recipe.
    """
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return abort(500, description='There was an issue displaying your recipe')
    else:
        return render_template('view.html', task=task)


def openAI_prompt(option_a, option_b, option_c, option_d):
    """Create a recipe prompt for the OpenAI API, using the given options.
    Args:
        option_a (str): The protein option to include in the recipe.
        option_b (str): Additional ingredient to include in the recipe.
        option_c (str): First cuisine style to include in the recipe.
        option_d (str): Second cuisine style to include in the recipe.

    Returns:
        str: A recipe prompt in the required format, with the given options included.
    """
    prompt = (f'Create a detailed recipe in the style of {option_c} and {option_d}, that uses {option_a} for the protein, includes {option_b}, and a reasonable quantity of salt. Make sure to include {option_c} incredients and {option_d} ingredients. Please write the ingredients and instructions in the format of a recipe. Use detailed instructions. Please format the recipe list as follows:\n\n'
              f'Instructions: [instructions]\n\n'
              f'Ingredients:\n[ingredients]\n\n'
              f"Ingredients:\n"
              f"- Ingredient 1\n"
              f"- Ingredient 2\n"
              f"\nInstructions:\n"
              f"1. Step 1\n"
              f"2. Step 2\n"
              f"3. Step 3\n\n"
            )
    return prompt


if __name__ == "__main__":
    app.run(debug=True)
