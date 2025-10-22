"""
fashion-app メインアプリケーション
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
import uuid

from config import Config
from models import db, Clothing, Settings, Schedule
from utils import get_weather_info, generate_outfit_suggestions


def create_app(config_class=Config):
    """アプリケーションファクトリ"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # データベース初期化
    db.init_app(app)
    
    # アップロードフォルダが存在しない場合は作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # データベーステーブル作成
    with app.app_context():
        db.create_all()
    
    # ===== ユーティリティ関数 =====
    
    def allowed_file(filename):
        """許可されたファイル拡張子かチェック"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    # ===== ルート定義 =====
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        """ホーム画面（提案画面）"""
        today = date.today()
        
        # 今日の予定をカレンダーから取得
        today_schedule = Schedule.query.filter_by(date=today).first()
        
        # 手動選択またはカレンダーからの予定を使用
        if request.method == 'POST':
            # 手動で予定を選択した場合
            selected_purpose = request.form.get('purpose')
            session['purpose'] = selected_purpose
            auto_selected = False
        elif today_schedule:
            # カレンダーに予定がある場合は自動選択
            selected_purpose = today_schedule.purpose
            auto_selected = True
        else:
            # カレンダーに予定がない場合はセッションまたはデフォルト
            selected_purpose = session.get('purpose', '大学')
            auto_selected = False
        
        # 天気情報取得（位置情報がある場合は使用）
        user_lat = session.get('user_latitude')
        user_lon = session.get('user_longitude')
        user_city = session.get('user_city')
        
        if user_lat and user_lon:
            weather = get_weather_info(latitude=user_lat, longitude=user_lon)
        else:
            weather = get_weather_info(city=user_city)
        
        # 服のリストを取得
        all_clothes = Clothing.query.all()
        
        # コーディネート提案を生成
        suggestions = []
        if weather['temperature'] is not None and all_clothes:
            suggestions = generate_outfit_suggestions(
                all_clothes, 
                selected_purpose, 
                weather['temperature'],
                count=3
            )
        
        return render_template(
            'index.html',
            weather=weather,
            selected_purpose=selected_purpose,
            suggestions=suggestions,
            today_schedule=today_schedule,
            auto_selected=auto_selected
        )
    
    @app.route('/closet')
    def closet():
        """クローゼット一覧画面"""
        clothes = Clothing.query.order_by(Clothing.created_at.desc()).all()
        return render_template('closet.html', clothes=clothes)
    
    @app.route('/closet/new')
    def closet_new():
        """服登録画面"""
        return render_template('closet_form.html', clothing=None)
    
    @app.route('/closet/add', methods=['POST'])
    def closet_add():
        """服登録処理"""
        # バリデーション
        if 'photo' not in request.files:
            flash('写真を選択してください', 'error')
            return redirect(url_for('closet_new'))
        
        photo = request.files['photo']
        if photo.filename == '':
            flash('写真を選択してください', 'error')
            return redirect(url_for('closet_new'))
        
        if not allowed_file(photo.filename):
            flash('許可されていないファイル形式です', 'error')
            return redirect(url_for('closet_new'))
        
        # 必須項目チェック
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        color = request.form.get('color')
        purposes = request.form.getlist('purposes')
        
        if not all([category, subcategory, color, purposes]):
            flash('全ての必須項目を入力してください', 'error')
            return redirect(url_for('closet_new'))
        
        # ファイル保存
        filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        
        # データベースには相対パスを保存
        relative_path = f"uploads/{filename}"
        
        # DB保存
        purposes_str = ','.join(purposes)
        new_clothing = Clothing(
            photo_path=relative_path,
            category=category,
            subcategory=subcategory,
            color=color,
            purposes=purposes_str,
            last_worn_date=None
        )
        
        db.session.add(new_clothing)
        db.session.commit()
        
        flash('服を登録しました', 'success')
        return redirect(url_for('closet'))
    
    @app.route('/closet/edit/<string:clothing_id>')
    def closet_edit(clothing_id):
        """服編集画面"""
        clothing = Clothing.query.get_or_404(clothing_id)
        return render_template('closet_form.html', clothing=clothing)
    
    @app.route('/closet/update/<string:clothing_id>', methods=['POST'])
    def closet_update(clothing_id):
        """服更新処理"""
        clothing = Clothing.query.get_or_404(clothing_id)
        
        # 必須項目チェック
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        color = request.form.get('color')
        purposes = request.form.getlist('purposes')
        
        if not all([category, subcategory, color, purposes]):
            flash('全ての必須項目を入力してください', 'error')
            return redirect(url_for('closet_edit', clothing_id=clothing_id))
        
        # 写真が新しくアップロードされた場合
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '' and allowed_file(photo.filename):
                # 古い画像を削除
                old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                            clothing.photo_path.replace('uploads/', ''))
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
                
                # 新しい画像を保存
                filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                clothing.photo_path = f"uploads/{filename}"
        
        # 更新
        clothing.category = category
        clothing.subcategory = subcategory
        clothing.color = color
        clothing.purposes = ','.join(purposes)
        
        db.session.commit()
        
        flash('服を更新しました', 'success')
        return redirect(url_for('closet'))
    
    @app.route('/closet/delete/<string:clothing_id>', methods=['POST'])
    def closet_delete(clothing_id):
        """服削除処理"""
        clothing = Clothing.query.get_or_404(clothing_id)
        
        # 画像ファイルを削除
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                clothing.photo_path.replace('uploads/', ''))
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        # データベースから削除
        db.session.delete(clothing)
        db.session.commit()
        
        flash('服を削除しました', 'success')
        return redirect(url_for('closet'))
    
    @app.route('/wear-outfit', methods=['POST'])
    def wear_outfit():
        """着用記録処理"""
        top_id = request.form.get('top_id')
        bottom_id = request.form.get('bottom_id')
        
        if not top_id or not bottom_id:
            flash('コーディネートの情報が不正です', 'error')
            return redirect(url_for('index'))
        
        # 最終着用日を今日に更新
        today = date.today()
        
        top = Clothing.query.get(top_id)
        bottom = Clothing.query.get(bottom_id)
        
        if top:
            top.last_worn_date = today
        if bottom:
            bottom.last_worn_date = today
        
        db.session.commit()
        
        flash('着用記録を保存しました！', 'success')
        return redirect(url_for('index'))
    
    @app.route('/reset-worn-date/<string:clothing_id>', methods=['POST'])
    def reset_worn_date(clothing_id):
        """個別の着用記録をリセット"""
        clothing = Clothing.query.get_or_404(clothing_id)
        clothing.last_worn_date = None
        db.session.commit()
        
        flash(f'{clothing.category}の着用記録をリセットしました', 'success')
        return redirect(url_for('closet'))
    
    @app.route('/reset-all-worn-dates', methods=['POST'])
    def reset_all_worn_dates():
        """全ての着用記録を一括リセット"""
        clothes = Clothing.query.filter(Clothing.last_worn_date.isnot(None)).all()
        count = len(clothes)
        
        for clothing in clothes:
            clothing.last_worn_date = None
        
        db.session.commit()
        
        flash(f'{count}件の着用記録をリセットしました', 'success')
        return redirect(url_for('closet'))
    
    @app.route('/calendar')
    def calendar():
        """カレンダー画面（予定一覧）"""
        # 今日以降の予定を取得
        today = date.today()
        schedules = Schedule.query.filter(Schedule.date >= today).order_by(Schedule.date).all()
        
        # 過去の予定も取得（オプション）
        past_schedules = Schedule.query.filter(Schedule.date < today).order_by(Schedule.date.desc()).limit(10).all()
        
        return render_template(
            'calendar.html',
            schedules=schedules,
            past_schedules=past_schedules,
            today=today
        )
    
    @app.route('/calendar/new')
    def calendar_new():
        """予定追加画面"""
        return render_template('calendar_form.html', schedule=None)
    
    @app.route('/calendar/add', methods=['POST'])
    def calendar_add():
        """予定追加処理"""
        schedule_date = request.form.get('date')
        purpose = request.form.get('purpose')
        memo = request.form.get('memo', '')
        
        if not schedule_date or not purpose:
            flash('日付と予定は必須です', 'error')
            return redirect(url_for('calendar_new'))
        
        # 日付をdate型に変換
        try:
            schedule_date = datetime.strptime(schedule_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日付の形式が正しくありません', 'error')
            return redirect(url_for('calendar_new'))
        
        # 同じ日に予定が既に存在するかチェック
        existing = Schedule.query.filter_by(date=schedule_date).first()
        if existing:
            flash(f'{schedule_date.strftime("%Y年%m月%d日")}には既に予定が登録されています', 'error')
            return redirect(url_for('calendar_new'))
        
        # 予定を保存
        new_schedule = Schedule(
            date=schedule_date,
            purpose=purpose,
            memo=memo
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        flash('予定を追加しました', 'success')
        return redirect(url_for('calendar'))
    
    @app.route('/calendar/edit/<string:schedule_id>')
    def calendar_edit(schedule_id):
        """予定編集画面"""
        schedule = Schedule.query.get_or_404(schedule_id)
        return render_template('calendar_form.html', schedule=schedule)
    
    @app.route('/calendar/update/<string:schedule_id>', methods=['POST'])
    def calendar_update(schedule_id):
        """予定更新処理"""
        schedule = Schedule.query.get_or_404(schedule_id)
        
        schedule_date = request.form.get('date')
        purpose = request.form.get('purpose')
        memo = request.form.get('memo', '')
        
        if not schedule_date or not purpose:
            flash('日付と予定は必須です', 'error')
            return redirect(url_for('calendar_edit', schedule_id=schedule_id))
        
        # 日付をdate型に変換
        try:
            schedule_date = datetime.strptime(schedule_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日付の形式が正しくありません', 'error')
            return redirect(url_for('calendar_edit', schedule_id=schedule_id))
        
        # 同じ日に別の予定が既に存在するかチェック
        existing = Schedule.query.filter(
            Schedule.date == schedule_date,
            Schedule.id != schedule_id
        ).first()
        if existing:
            flash(f'{schedule_date.strftime("%Y年%m月%d日")}には既に別の予定が登録されています', 'error')
            return redirect(url_for('calendar_edit', schedule_id=schedule_id))
        
        # 更新
        schedule.date = schedule_date
        schedule.purpose = purpose
        schedule.memo = memo
        
        db.session.commit()
        
        flash('予定を更新しました', 'success')
        return redirect(url_for('calendar'))
    
    @app.route('/calendar/delete/<string:schedule_id>', methods=['POST'])
    def calendar_delete(schedule_id):
        """予定削除処理"""
        schedule = Schedule.query.get_or_404(schedule_id)
        
        db.session.delete(schedule)
        db.session.commit()
        
        flash('予定を削除しました', 'success')
        return redirect(url_for('calendar'))
    
    @app.route('/update-location', methods=['POST'])
    def update_location():
        """位置情報を更新して天気を取得"""
        try:
            data = request.get_json()
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            city = data.get('city')
            
            if not latitude or not longitude:
                return jsonify({'success': False, 'error': '位置情報が不正です'})
            
            # セッションに位置情報を保存
            session['user_latitude'] = latitude
            session['user_longitude'] = longitude
            if city:
                session['user_city'] = city
            
            return jsonify({'success': True})
            
        except Exception as e:
            app.logger.error(f"Location update error: {e}")
            return jsonify({'success': False, 'error': 'サーバーエラーが発生しました'})
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)

