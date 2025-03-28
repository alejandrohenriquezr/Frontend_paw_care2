from flask import Flask, render_template
from config import Config
from app import app  # Importamos la instancia de Flask desde app.py

app.config.from_object(Config)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
