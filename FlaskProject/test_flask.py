from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <h1>🎉 SUCCESS! Flask is working!</h1>
    <p>Your Flask application is running correctly.</p>
    <p>Time to go back to the main application!</p>
    """

if __name__ == '__main__':
    print("🚀 Testing Flask...")
    print("📱 Open: http://127.0.0.1:6000")
    app.run(debug=True)