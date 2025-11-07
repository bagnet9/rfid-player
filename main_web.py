import os
import mmap
from flask import Flask, render_template, request, redirect
import json
import threading
app = Flask(__name__)
app.config['MUSIC_FOLDER'] = './Music'

def read_uuid():
    with open('shared_data.dat', 'r+b') as f:
        with mmap.mmap(f.fileno(), 1024, access=mmap.ACCESS_READ) as mm:
            mm.seek(0)
            data = mm.readline().rstrip(b'\0')
            return data.decode('utf-8')

@app.route('/check_uuid')
def check_uuid():
    return read_uuid()

@app.route('/')
def main():
    with open('shared_data.dat', 'r+b') as f:
        uuid = read_uuid()
        music = ""
        musics = os.listdir(app.config['MUSIC_FOLDER'])
        print(musics)
        with open('UID_TO_TRACK.json', 'r') as json_file:
            uid_to_track = json.load(json_file)
            print(uid_to_track)
            if uuid in uid_to_track:
                music = uid_to_track[uuid]
                # remove the extension
                music = music.split('.')[0]
            return render_template('index.html',uuid=uuid, music=music,musics=musics)

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload by adding it to the UPLOAD_FOLDER.
    """
    f = request.files['music_file']
    f.save(os.path.join(app.config['MUSIC_FOLDER'], f.filename))
    return redirect('/')

@app.route("/change_music",methods=['POST'])
def change_music():
    with open('shared_data.dat', 'r+b') as f:
        with mmap.mmap(f.fileno(), 1024, access=mmap.ACCESS_READ) as mm:
            mm.seek(0)
            data = mm.readline().rstrip(b'\0')
            print("uuid :" + data.decode('utf-8'))
            selected_music = request.form['music_name']
            with open('UID_TO_TRACK.json', 'r+') as json_file:
                uid_to_track = json.load(json_file)
                uid_to_track[data.decode('utf-8')] = selected_music
                json_file.seek(0)
                json.dump(uid_to_track, json_file)
                json_file.truncate()
    return redirect('/')
# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0',port=8080,debug=True)


