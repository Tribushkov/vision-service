import os
import cv2
import time;
from flask import Flask, request, redirect, url_for, flash, send_from_directory, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['mp4', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/uploads/<path:path>')
def serve(path):
    return send_from_directory('uploads', path)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Step 1: upload a video file
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            #flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            #flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('video_process',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Step 1</title>
    <h2>Upload new video file</h2>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


# Step 2: split on frames
@app.route('/video_process', methods=['GET', 'POST'])
def video_process():
    filename = request.args.get('filename')
    if request.method == 'POST':
	    return redirect(url_for('frames', filename=filename))
    return '''
    <!doctype html>
    <title>Step 2</title>
    <h2><a href=/uploads/{:s}>Video</a> successfully uploaded</h2>
    <form method=post>
      <p>
         <input type=submit value='Split on frames'>
    </form>
    '''.format(filename)


def extractFrames(pathIn, pathOut):
    os.mkdir(pathOut)
    cap = cv2.VideoCapture(pathIn)
    count = 0
    while (cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            print('Read %d frame: ' % count, ret)
            cv2.imwrite(os.path.join(pathOut, "frame{:d}.jpg".format(count)), frame)  # save frame as JPEG file
            count += 1
        else:
            break
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


# Split on frames here
@app.route('/frames')
def frames():
	filename = request.args.get('filename')
	ts = time.time()
	image_folder = 'static/data/images' + str(ts)
	extractFrames('uploads/' + filename, image_folder)
	return redirect(url_for('region', image_folder=image_folder))


# Select dangerous zone
@app.route('/region', methods=['GET', 'POST'])
def region():
	image_folder = request.args.get('image_folder')
	filename = image_folder + '/frame0.jpg'
	if request.method == 'POST':
		x1 = request.form.get('x1')
		x2 = request.form.get('x2')
		y1 = request.form.get('y1')
		y2 = request.form.get('y2')
		return redirect(url_for('table', image_folder=image_folder, x1=x1, x2=x2, y1=y1, y2=y2))
	return render_template("region.html", filename = filename)


# Final table with something #TBD Vision REST API
@app.route('/table')
def table():
    image_folder = request.args.get('image_folder')
    x1 = request.args.get('x1')
    x2 = request.args.get('x2')
    y1 = request.args.get('y1')
    y2 = request.args.get('y2')
    files = os.listdir(image_folder)
    image_count = len(files)

    # send rest api requests in this loop
    #for i in range(0, image_count):
        #print (image_folder + '/frame' + str(i) + '.jpg')

    return render_template("table.html", image_folder=image_folder, x1=x1, x2=x2, y1=y1, y2=y2, image_count=image_count)


if __name__ == '__main__':
    app.debug = True
    app.run()