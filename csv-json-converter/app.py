"""CSV to JSON Converter — Flask Application Entry Point."""

import sys
from pathlib import Path

from flask import Flask

# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Ensure project root is available for imports
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

from config.config import (
    SECRET_KEY,
    DEBUG,
    UPLOAD_FOLDER,
    OUTPUT_FOLDER,
    MAX_FILE_SIZE_BYTES,
)

from routes.converter import converter_bp


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    # --------------------------------------------------------
    # Flask configuration
    # --------------------------------------------------------

    app.secret_key = SECRET_KEY
    app.debug = DEBUG

    # Maximum request/upload size
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES

    # Upload and output directories
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["OUTPUT_FOLDER"] = str(OUTPUT_FOLDER)

    # --------------------------------------------------------
    # Create required directories
    # --------------------------------------------------------

    UPLOAD_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Register application routes
    # --------------------------------------------------------

    app.register_blueprint(converter_bp)

    # ========================================================
    # ERROR HANDLERS
    # ========================================================

    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad requests."""

        return {
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": "The request could not be processed.",
            },
        }, 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle requests for non-existent routes."""

        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
            },
        }, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle unsupported HTTP methods."""

        return {
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The HTTP method is not allowed for this endpoint.",
            },
        }, 405

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle files larger than the configured limit."""

        max_size_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)

        return {
            "success": False,
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": (
                    f"The file exceeds the maximum allowed size "
                    f"of {max_size_mb:g} MB."
                ),
            },
        }, 413

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle unexpected server errors."""

        return {
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An internal server error occurred.",
            },
        }, 500

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    @app.route("/health", methods=["GET"])
    def health_check():
        """Return application health status."""

        return {
            "success": True,
            "status": "healthy",
            "service": "csv-to-json-converter",
        }, 200

    return app


# ============================================================
# APPLICATION INSTANCE
# ============================================================

app = create_app()


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    max_upload_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)

    print()
    print("  CSV -> JSON Converter")
    print("  " + "=" * 40)
    print("  Server:      http://127.0.0.1:5000")
    print(
        f"  Environment: "
        f"{'Development' if DEBUG else 'Production'}"
    )
    print(
        f"  Max upload:  "
        f"{max_upload_mb:g} MB"
    )
    print("  Health:      http://127.0.0.1:5000/health")
    print("  " + "=" * 40)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=DEBUG,
    )

