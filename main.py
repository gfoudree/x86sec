from flask import Flask, render_template, make_response
app = Flask(__name__)

headers = {'X-Frame-Sptions' : 'SAMEORIGIN',
			'X-XSS-Protection' : '1; mode=block',
			'X-Content-Type-Options' : 'nosniff',
			'Content-Security-Policy' : 'default-src \'none\'; style-src *.x86sec.com; font-src https://fonts.googleapis.com; img-src *.x86sec.com;',
			'Referrer-Policy' : 'same-origin'
		}

@app.route('/')
def index():
	return render_template('index.html'), 200, headers

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
