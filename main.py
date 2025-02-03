from sqlalchemy.exc import IntegrityError
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
  pass
db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-collection-new.db"
db.init_app(app)
class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10. e.g 7.5',validators=[DataRequired()])
    review=StringField('Review',validators=[DataRequired()])
    update=SubmitField(label='Update')

class AddForm(FlaskForm):
    title=StringField('Enter Movie Title',validators=[DataRequired()])
    add = SubmitField(label='Add Movie')


# CREATE TABLE
class Movie(db.Model):
    __tablename__ = "movie"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    year:  Mapped[int] = mapped_column(nullable=True)
    description : Mapped[str] = mapped_column(nullable=True)
    rating : Mapped[float] = mapped_column(nullable=True)
    ranking : Mapped[int] = mapped_column(nullable=True)
    review: Mapped[str] = mapped_column(nullable=True)
    img_url: Mapped[str] = mapped_column(nullable=True)
with app.app_context():
    db.create_all()
HEADERS = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNmUwZDM5NmVlOWM2YWJhNjQ1YzA0ZGM0ZTFhYTdmNCIsIm5iZiI6MTczODI2MzYzMC41NjMsInN1YiI6IjY3OWJjYzRlOTAwNTI1MjQ5YWZiZTQwNiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.AKUbxNnxTsgYUTKZWYpvNO8SK-tAKbWJroc4q-vNeUQ"
    }

@app.route("/")
def home():
    movies=db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(movies)):
        movies[i].ranking=len(movies)-i
    db.session.commit()

    return render_template("index.html",movie=movies)

@app.route('/edit/<movie_id>',methods=['POST','GET'])
def edit(movie_id):

    form=EditForm()
    if form.validate_on_submit():
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        movie_to_update.rating = request.form['rating']
        movie_to_update.review=request.form['review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html',form=form)

@app.route("/delete/<movie_id>",methods=['POST','GET'])
def delete(movie_id):
    movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))
@app.route('/add',methods=['POST','GET'])
def add_movie():
    form=AddForm()
    if form.validate_on_submit():
        return redirect(url_for('select_movie',movie_title=request.form['title']))
    return render_template('add.html',form=form)


@app.route("/select/<movie_title>")
def select_movie(movie_title):
    url = "https://api.themoviedb.org/3/search/movie"
    params={
        "query":movie_title
    }

    response = requests.get(url, headers=HEADERS,params=params)
    movie_collection=response.json()["results"]
    print(response.json()["results"][0]["original_title"])

    return render_template('select.html',movies=movie_collection)

@app.route("/find")
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"

        response=requests.get(movie_url,headers=HEADERS)
        data=response.json()
        movie_image_url = 'https://image.tmdb.org/t/p/original'
        try:
            new_movie=Movie(title=data['original_title'],year=data['release_date'],img_url=f'{movie_image_url}{data['poster_path']}',
                        description=data['overview'])

            db.session.add(new_movie)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return render_template('error.html')
        else:
            return redirect(url_for('edit',movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
