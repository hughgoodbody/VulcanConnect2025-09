# app/main.py

from . import create_app

app = create_app()

@app.route("/testapi")
def testapi():
    return {"status": "ok"}

# Optional: for local dev: `python -m app.main`
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

