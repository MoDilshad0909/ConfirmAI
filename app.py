import os
import logging
import traceback
from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
from flask_migrate import Migrate
from config import config_map
from models import db
from utils.errors import APIError


def create_app(env: str = None) -> Flask:
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app.logger.setLevel(logging.INFO)

    db.init_app(app)
    Migrate(app, db)
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    # Register models so migrate can detect them
    from models.user import User
    from models.train import Train
    from models.station import Station
    from models.prediction import Prediction, SearchHistory

    # Initialize ML model pipeline globally
    with app.app_context():
        from services.prediction_service import init_pipeline
        init_pipeline(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.predict import predict_bp
    from routes.admin import admin_bp
    from routes.metadata import metadata_bp
    from routes.profile import profile_bp
    from routes.admin_api import admin_api_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(admin_api_bp, url_prefix="/api")
    app.register_blueprint(metadata_bp, url_prefix="/api")
    app.register_blueprint(profile_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/profile")
    def profile_page():
        return render_template("profile.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/result")
    def result():
        return render_template("result.html")

    @app.route("/history")
    def history():
        return render_template("history.html")

    @app.route("/admin")
    def admin():
        import datetime
        apk_path = os.path.join(app.root_path, "static", "downloads", "confirmai.apk")
        apk_exists = os.path.exists(apk_path)
        apk_size = round(os.path.getsize(apk_path) / (1024 * 1024), 2) if apk_exists else 0.0
        build_date = datetime.datetime.fromtimestamp(os.path.getmtime(apk_path)).strftime('%Y-%m-%d %H:%M:%S') if apk_exists else "N/A"
        return render_template("admin.html", apk_exists=apk_exists, apk_size=apk_size, build_date=build_date, apk_version="1.0.0")

    @app.route("/download-app")
    def download_app():
        downloads_dir = os.path.join(app.root_path, "static", "downloads")
        return send_from_directory(
            downloads_dir, 
            "confirmai.apk", 
            as_attachment=True,
            mimetype='application/vnd.android.package-archive'
        )

    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.route("/admin/debug")
    def admin_debug():
        from models.user import User
        from models.prediction import Prediction, SearchHistory
        from models import db
        from flask import jsonify

        try:
            db.session.execute(db.text("SELECT 1"))
            db_status = "Connected"
        except Exception as e:
            db_status = f"Disconnected: {str(e)}"
            
        return jsonify({
            "db_status": db_status,
            "user_count": User.query.count(),
            "prediction_count": Prediction.query.count(),
            "search_count": SearchHistory.query.count(),
            "latest_20_users": [u.to_dict() for u in User.query.order_by(User.user_id.desc()).limit(20).all()],
            "latest_20_predictions": [p.to_dict() for p in Prediction.query.order_by(Prediction.prediction_id.desc()).limit(20).all()],
            "latest_20_searches": [{"src": s.source_station, "dest": s.destination_station, "time": s.searched_at.isoformat()} for s in SearchHistory.query.order_by(SearchHistory.search_id.desc()).limit(20).all()]
        })

    @app.route("/profile")
    def profile():
        return render_template("profile.html")

    @app.before_request
    def log_website_traffic():
        if request.endpoint and (request.endpoint.startswith("static") or request.endpoint == "health"):
            return
        
        try:
            from models.analytics import WebsiteAnalytics
            from utils.jwt_utils import decode_token
            from models import db
            
            is_logged_in = False
            user_id = None
            
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                try:
                    payload = decode_token(auth.split(" ", 1)[1])
                    user_id = payload.get("user_id")
                    is_logged_in = True
                except Exception:
                    pass
                    
            user_agent = request.headers.get('User-Agent', '')
            device = "Mobile" if "Mobi" in user_agent else "Tablet" if "Tablet" in user_agent else "Desktop"
            visitor_id = request.cookies.get("visitor_id") or request.remote_addr
            
            log = WebsiteAnalytics(
                visitor_id=visitor_id,
                is_logged_in=is_logged_in,
                user_id=user_id,
                device_type=device,
                browser=user_agent[:100],
                endpoint=request.endpoint,
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    @app.api_route("/api/health", methods=["GET"]) if hasattr(app, "api_route") else app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"success": True, "data": {"status": "ok", "service": "RailWise AI"}}), 200

    @app.errorhandler(APIError)
    def handle_api_error(e):
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        return response

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Route not found"}), 404
        return render_template("index.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled Exception: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)
