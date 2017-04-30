from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/projects')
def projects():
	return render_template('projects.html')
	
@app.route('/posts')
def posts():
	return render_template('posts.html')

@app.route('/downloads')
def downloads():
	return render_template('downloads.html')

@app.route('/about')
def about():
	return render_template('about.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
