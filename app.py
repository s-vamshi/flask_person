from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import face_recognition
from PIL import Image
from io import BytesIO
import base64


app = Flask(__name__)

app.secret_key = "abc"  

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///missing.db"
db = SQLAlchemy(app)

class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        image = request.files['image']

        # Convert the image to a binary object
        image_binary = image.read()

        missing_person = MissingPerson(name=name, location=location, image=image_binary)
        db.session.add(missing_person)
        db.session.commit()

        return redirect(url_for('registration_success'))
    return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        location = request.form['location']
        image = request.files['image']

        # Load the uploaded image and encode it
        uploaded_image = face_recognition.load_image_file(image)
        if(len(face_recognition.face_encodings(uploaded_image))==0):
            return redirect(url_for('not_found'))
        uploaded_image_encoding = face_recognition.face_encodings(uploaded_image)[0]

        # Find all missing persons in the given location
        missing_persons = MissingPerson.query.filter_by().all()

        # Iterate over the missing persons and check if the uploaded image matches any of them
        for missing_person in missing_persons:
            # Load the missing person's image and encode it
            missing_person_image = face_recognition.load_image_file(BytesIO(missing_person.image))
            missing_person_image_encoding = face_recognition.face_encodings(missing_person_image)[0]
            # Check if the uploaded image matches the missing person's image
            result = face_recognition.compare_faces([uploaded_image_encoding], missing_person_image_encoding)
            if result[0]:
                # If the uploaded image matches the missing person's image, redirect to the success page
                return redirect(url_for('success', name=missing_person.name))   

        # If no missing persons were found, redirect to the not_found page
        return redirect(url_for('not_found'))
    return render_template('search.html')

@app.route('/missing_persons')
def missing_persons():
    # Get all missing persons from the database
    missing_persons = MissingPerson.query.all()

    # Convert each missing person's image to a base64 string
    for missing_person in missing_persons:
        image_file = BytesIO(missing_person.image)
        image_data = base64.b64encode(image_file.getvalue()).decode('utf-8')
        missing_person.image = "data:image/jpeg;base64,{}".format(image_data)

    return render_template('missing_persons.html', missing_persons=missing_persons)

@app.route('/registration_success')
def registration_success():
    return render_template('registration_success.html')

@app.route('/success/<name>')
def success(name):
    missing_person = MissingPerson.query.filter_by(name=name).first()
    image = missing_person.image

    # Convert the image from a binary object to an image file
    image_file = BytesIO(image)
    image = Image.open(image_file)

    # Encode the image as a base64 string
    image_data = base64.b64encode(image_file.getvalue()).decode('utf-8')
    image_data = "data:image/jpeg;base64,{}".format(image_data)

    return render_template('success.html', name=name, image=image_data)



@app.route('/not_found')
def not_found():
    return render_template('not_found.html')

if __name__ == '__main__':
  app.run(debug=True)

