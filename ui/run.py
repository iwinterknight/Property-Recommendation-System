from flask import Flask, render_template, request, jsonify
from flask_cors import CORS


from src.dialogagent.llm_prompts import generate_response
app = Flask(__name__)
CORS(app)


# @app.get("/")
@app.route("/", methods=["GET"])
def index_get():
    return render_template("base.html")


# @app.post("/predict")
@app.route("/predict", methods=["POST"])
def predict():
    text = request.get_json(force=True).get("message")
    response = generate_response(text)
    # response = None
    message = {"answer": response}
    return jsonify(message)


if __name__=="__main__":
    app.run(debug=True)