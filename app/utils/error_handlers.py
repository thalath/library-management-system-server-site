from flask import request, jsonify

def registered_error_handlers(app):

    @app.errorhandler(404)
    def handle_error_not_found(error):
        return jsonify({
            "messages": "This HTTP request URL not found.",
            "error": "file not found.",
            "status": 404,
            "path": request.path,
            "method": request.method
        }), 404

    @app.errorhandler(405)
    def handle_error_method_not_allowed(error):
        return jsonify({
            "message": f"This HTTP request URL not allowed to use {request.method} method.",
            "error": "method not allowed.",
            "status": 405,
            "path": request.path
        }), 405

    @app.errorhandler(500)
    def handle_error_internal_server_error(error):
        return jsonify({
            "message": "Server error accured.",
            "error": "Internal server error.",
            "status": 500,
            "path": request.path
        }), 500
