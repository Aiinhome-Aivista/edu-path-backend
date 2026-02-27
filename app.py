from flask_cors import CORS
from flask import Flask, jsonify

app = Flask(__name__)
CORS(app)

# -----------------------------
# Example Route
# -----------------------------
@app.route("/health")
def health():
    return jsonify({
        "status": "OK"
    })




# -----------------------------
# Run App on Port 3019
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3019, debug=True)