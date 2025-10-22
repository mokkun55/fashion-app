"""
アプリケーション設定
"""
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


class Config:
    """アプリケーション設定クラス"""
    
    # Flask設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'fashion_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ファイルアップロード設定
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # OpenWeatherMap API設定
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    DEFAULT_CITY = os.environ.get('DEFAULT_CITY') or 'Tokyo'

