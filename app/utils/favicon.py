from flask import send_from_directory
def get_favicon(app):
    
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            app.static_folder,
            "favicon.png",
            mimetype="image\png"
        )

