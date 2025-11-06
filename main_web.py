import os

from flask import Flask, render_template, request

app = Flask(__name__)
app.config['MUSIC_FOLDER'] = './Music'
@app.route('/')
def main():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload by adding it to the UPLOAD_FOLDER.
    """
    f = request.files['music_file']
    f.save(os.path.join(app.config['MUSIC_FOLDER'], f.filename))
    return render_template('upload.html')

# main driver function
if __name__ == '__main__':

    # run() method of Flask class runs the application
    # on the local development server.
    app.run()


