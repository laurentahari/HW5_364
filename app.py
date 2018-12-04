import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField, IntegerField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

############################
# Application configurations
############################
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hard to guess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

## Your final Postgres database should be your uniqname, plus HW5, e.g. "jczettaHW5" or "maupandeHW5"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/taharilHW5"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


#########################
##### Set up Models #####
#########################

## All provided.

# Association table
on_list = db.Table('on_list',db.Column('item_id',db.Integer, db.ForeignKey('items.id')),db.Column('list_id',db.Integer, db.ForeignKey('lists.id')))

class TodoList(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(225))
    items = db.relationship('TodoItem',secondary=on_list,backref=db.backref('lists',lazy='dynamic'),lazy='dynamic')

class TodoItem(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(225))
    priority = db.Column(db.Integer)


########################
##### Set up Forms #####
########################

# Provided - Form to create a todo list
class TodoListForm(FlaskForm):
    name = StringField("What is the title of this TODO List?", validators=[Required()])
    items = TextAreaField("Enter your TODO list items in the following format: Description,Priority -- separated by a comma")
    submit = SubmitField("Submit")

# TODO 364: Define an UpdateButtonForm class for use to update todo items
class UpdateButtonForm(FlaskForm):
    updateitem = TextAreaField("Enter your updated TODO list item in the following format: Description,Priority -- separated by a comma")
    submit = SubmitField("Update")


# TODO 364: Define a form class for updating the priority of a todolist item
#(HINT: What class activity you have done before is this similar to?)
class UpdatePriority(FlaskForm):
    priority = IntegerField('What is the updated priority of this item?', validators=[Required()])
    submit = SubmitField('Update')


# TODO 364: Define a DeleteButtonForm class for use to delete todo items
class DeleteButtonForm(FlaskForm):
    submit = SubmitField('Delete')


################################
####### Helper Functions #######
################################

## Provided.

def get_or_create_item(item_string):
    elements = [x.strip().rstrip() for x in item_string.split(",")]
    item = TodoItem.query.filter_by(description=elements[0]).first()
    if item:
        return item
    else:
        item = TodoItem(description=elements[0],priority=elements[-1])
        db.session.add(item)
        db.session.commit()
        return item

def get_or_create_todolist(title, item_strings=[]):
    l = TodoList.query.filter_by(title=title).first()
    if not l:
        l = TodoList(title=title)
    for s in item_strings:
        item = get_or_create_item(s)
        l.items.append(item)
    db.session.add(l)
    db.session.commit()
    return l


###################################
##### Routes & view functions #####
###################################

# Provided
@app.route('/', methods=["GET","POST"])
def index():
    form = TodoListForm()
    if request.method=="POST":
        title = form.name.data
        items_info = form.items.data
        newlist = get_or_create_todolist(title, items_info.split("\n"))
        return redirect(url_for('all_lists'))
    return render_template('index.html',form=form)

# Provided - see below for additional TODO
# TODO 364: Update the all_lists.html template and the all_lists view function such that there is a delete button available for each ToDoList saved.
# When you click on the delete button for each list, that list should get deleted -- this is also addressed in a later TODO.
@app.route('/all_lists',methods=["GET","POST"])
def all_lists():
    form = DeleteButtonForm()
    lsts = TodoList.query.all()
    return render_template('all_lists.html',form=form,todo_lists=lsts)

# Provided - see below for additional TODO
# TODO 364: Update the one_list view function and the list_tpl.html view file so that there is an Update button next to each todolist item, and the priority integer of that item can be updated. (This is also addressed in later TODOs.)
# HINT: These template updates are minimal, but that small update(s) make(s) a big change in what you can do in the app! Check out the examples from previous classes for help.
@app.route('/list/<ident>',methods=["GET","POST"])
def one_list(ident):
    form = UpdateButtonForm()
    lst = TodoList.query.filter_by(id=ident).first()
    items = lst.items.all()
    return render_template('list_tpl.html',todo_lists=lst,items=items,form=form)

# TODO 364: Complete route to update an individual ToDo item's priority
    # This code should use the form you created above for updating the specific item and manage the process of updating the item's priority.
    # Once it is updated, it should redirect to the page showing all the links to todo lists.
    # It should flash a message: Updated priority of <the description of that item>
    # HINT: What previous class example is extremely similar?

# TODO 364: Fill in the update_item.html template to work properly with this update route. (HINT: Compare against example!)
@app.route('/update/<item>',methods=["GET","POST"])
def update(item):
    form = UpdatePriority()
    if form.validate_on_submit():
        newitems = TodoItem.query.filter_by(description=item).first()
        newitems.priority = form.priority.data
        db.session.commit()

        flash("Sucessfully updated the priority of: {}".format(item))
        return redirect(url_for("all_lists"))

    return render_template("update_item.html", form=form, item=item)



# TODO 364: Complete route to delete a whole ToDoList
    # This code should successfully delete the appropriate todolist
    # Should flash a message about what was deleted, e.g. Deleted list <title of list>
    # And should redirect the user to the page showing all the todo lists
    # HINT: Compare against what you've done for updating and class notes -- the goal here is very similar, and in some ways simpler.
@app.route('/delete/<lst>',methods=["GET","POST"])
def delete(lst):
    y= TodoList.query.filter_by(id=lst).first()
    title = y.title
    db.session.delete(y)
    db.session.commit()
    flash("Successfully deleted TODO list: {}".format(title))
    return redirect(url_for('all_lists'))


if __name__ == "__main__":
    db.create_all()
    manager.run()