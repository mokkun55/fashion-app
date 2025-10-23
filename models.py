"""
データベースモデル定義
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


class Clothing(db.Model):
    """服アイテムモデル"""
    __tablename__ = 'clothing'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_path = db.Column(db.String(255), nullable=False)  # 画像ファイルパス
    category = db.Column(db.String(20), nullable=False)  # "トップス" | "ボトムス"
    subcategory = db.Column(db.String(20), nullable=False)  # "半袖" | "長袖・薄手" | "長袖・厚手" | "短め" | "長め"
    color = db.Column(db.String(50), nullable=False)  # "黒" | "白" | etc.
    purposes = db.Column(db.String(100), nullable=False)  # カンマ区切り: "大学,企業,デート"
    last_worn_date = db.Column(db.Date, nullable=True)  # 最終着用日
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 登録日時
    
    # 自動検出された属性（JSON形式で保存）
    detected_colors = db.Column(db.Text, nullable=True)  # 検出された色の情報
    detected_category = db.Column(db.String(20), nullable=True)  # 自動検出されたカテゴリ
    detected_subcategory = db.Column(db.String(20), nullable=True)  # 自動検出されたサブカテゴリ
    detection_confidence = db.Column(db.Float, nullable=True)  # 検出の信頼度
    shape_analysis = db.Column(db.Text, nullable=True)  # 形状分析結果
    size_estimation = db.Column(db.Text, nullable=True)  # サイズ推定結果
    
    def get_purposes_list(self):
        """用途ラベルをリストで取得"""
        return self.purposes.split(',') if self.purposes else []
    
    def __repr__(self):
        return f'<Clothing {self.id}: {self.category} - {self.subcategory}>'


class Settings(db.Model):
    """アプリ設定モデル"""
    __tablename__ = 'settings'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<Settings {self.key}: {self.value}>'


class Schedule(db.Model):
    """予定管理モデル"""
    __tablename__ = 'schedule'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False)  # 予定の日付
    purpose = db.Column(db.String(20), nullable=False)  # "大学" | "企業" | "デート"
    memo = db.Column(db.String(200), nullable=True)  # メモ（オプション）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 登録日時
    
    def __repr__(self):
        return f'<Schedule {self.date}: {self.purpose}>'

