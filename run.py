from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    app.run(
            debug=False,
            port=os.environ.get("PORT", "5000"),
            host=os.environ.get("HOST", "0.0.0.0")
        )

