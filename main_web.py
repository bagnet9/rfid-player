import os
import mmap
from flask import Flask, render_template, request
import json
app = Flask(__name__)
app.config['MUSIC_FOLDER'] = './Music'
@app.route('/')
def main():
    with open('shared_data.dat', 'r+b') as f:
        with mmap.mmap(f.fileno(), 1024, access=mmap.ACCESS_READ) as mm:
            mm.seek(0)
            data = mm.readline().rstrip(b'\0')
            print("uuid :" + data.decode('utf-8'))
            music = ""
            musics = os.listdir(app.config['MUSIC_FOLDER'])
            print(musics)
            with open('UID_TO_TRACK.json', 'r') as json_file:
                uid_to_track = json.load(json_file)
                print(uid_to_track)
                if data.decode('utf-8') in uid_to_track:
                    music = uid_to_track[data.decode('utf-8')]
                    # remove the extension
                    music = music.split('.')[0]
            return render_template('index.html',uuid=data.decode('utf-8'), music=music,musics=musics)

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload by adding it to the UPLOAD_FOLDER.
    """
    f = request.files['music_file']
    f.save(os.path.join(app.config['MUSIC_FOLDER'], f.filename))
    return render_template('index.html')

# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0',port=8080,debug=True)


