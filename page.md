# ページ一覧

## 1. ホーム画面（提案画面）

### URL

`/` (ルート)

### 要件

- アプリケーションのメイン画面として機能する
- 当日の予定を設定し、それに基づいたコーディネートを提案する
- 提案されたコーデに対して着用記録を行う

### 仕様

#### 表示要素

1. **予定選択エリア**

   - 選択肢: `デート` / `企業` / `学校`
   - 単一選択（ラジオボタンまたはセグメントコントロール）
   - デフォルト: `学校`

2. **気温・天気情報表示エリア**

   - 外部天気 API から取得した現在の気温を表示
   - 気温に応じた補足メッセージ（15℃ 未満の場合は「アウターを羽織ることをおすすめします」）

3. **コーディネート提案エリア**

   - 3 パターンのコーデを表示
   - 各パターンには以下を表示:
     - トップスの写真
     - ボトムスの写真
     - 各アイテムの基本情報（色、種類）
   - 候補が不足する場合のエラーハンドリング

4. **アクション**
   - 各コーデに「これを着た」ボタンを配置
   - ボタン押下時、該当するトップスとボトムスの「最終着用日」を現在日時に更新

#### データ取得ロジック

1. 外部天気 API から現在の気温を取得
2. 選択された予定に基づき、該当する用途ラベルを持つ服を抽出
3. 気温に基づき、適切な種類（中分類）の服を絞り込み:
   - 28℃ 以上: トップス `半袖` / ボトムス `短め`
   - 20-28℃: トップス `長袖・薄手` / ボトムス `長め`
   - 15-20℃: トップス `長袖・厚手` / ボトムス `長め`
   - 15℃ 未満: トップス `長袖・厚手` / ボトムス `長め` + アウター推奨メッセージ
4. 最終着用日が直近 2 日以内の服を除外
5. 残った候補からランダムに 3 パターンのコーデを生成

---

## 2. クローゼット一覧画面

### URL

`/closet` または `/wardrobe`

### 要件

- 登録済みの服を一覧表示する
- 各服の編集・削除機能へアクセスできる
- 服の登録画面へ遷移できる

### 仕様

#### 表示要素

1. **ヘッダー**

   - ページタイトル: 「クローゼット」
   - 新規登録ボタン（服登録画面へ遷移）

2. **フィルター・ソート機能（オプション）**

   - 大分類でフィルタ: `全て` / `トップス` / `ボトムス`
   - 用途ラベルでフィルタ: `全て` / `デート` / `企業` / `大学`

3. **服アイテム一覧**

   - グリッドレイアウトで表示
   - 各アイテムカードには以下を表示:
     - 写真（サムネイル）
     - 大分類・中分類
     - 色
     - 用途ラベル（複数）
     - 最終着用日（着用済みの場合）
   - タップ/クリックで編集画面へ遷移

4. **空状態**
   - 服が登録されていない場合のメッセージ表示
   - 登録画面への誘導

#### データ表示

- SQLite データベースから全ての服データを取得
- フィルタリング条件に応じて表示内容を更新
- 写真は `static/uploads/` ディレクトリに保存されているため、表示時はファイルパスを使用

---

## 3. 服登録/編集画面

### URL

- 新規登録: `/closet/new` または `/closet/add`
- 編集: `/closet/edit/:id`

### 要件

- 服の情報を入力・編集するフォーム
- 写真のアップロード機能
- 入力バリデーション
- SQLite データベースへのデータ保存

### 仕様

#### 表示要素（フォーム項目）

1. **写真アップロード** (必須)

   - ファイル選択ボタン
   - プレビュー表示
   - 対応形式: jpg, png, webp 等の画像ファイル

2. **種類（大分類）** (必須)

   - 選択肢: `トップス` / `ボトムス`
   - ラジオボタンまたはセグメントコントロール

3. **種類（中分類）** (必須)

   - 大分類が `トップス` の場合: `半袖` / `長袖・薄手` / `長袖・厚手`
   - 大分類が `ボトムス` の場合: `短め` / `長め`
   - ドロップダウンまたはラジオボタン
   - 大分類の選択に応じて動的に選択肢を切り替え

4. **色** (必須)

   - テキスト入力、またはプリセット色の選択
   - 例: 黒, 白, 赤, 青, グレー, ベージュ, 茶色, etc.
   - 複数色の入力も考慮（Array 形式）

5. **用途ラベル** (必須)

   - 選択肢: `デート` / `企業` / `大学`
   - チェックボックスで複数選択可能
   - 最低 1 つ以上の選択必須

6. **アクションボタン**
   - `保存` ボタン: バリデーション後、SQLite データベースに保存
   - `キャンセル` ボタン: 一覧画面に戻る
   - 編集画面の場合、`削除` ボタンも表示

#### データ構造（SQLAlchemy モデル）

```python
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class Clothing(db.Model):
    __tablename__ = 'clothing'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_path = db.Column(db.String(255), nullable=False)  # 画像ファイルパス
    category = db.Column(db.String(20), nullable=False)  # "トップス" | "ボトムス"
    subcategory = db.Column(db.String(20), nullable=False)  # "半袖" | "長袖・薄手" | etc.
    color = db.Column(db.String(50), nullable=False)  # "黒" | "白" | etc.
    purposes = db.Column(db.String(100), nullable=False)  # カンマ区切り: "学校,企業,デート"
    last_worn_date = db.Column(db.Date, nullable=True)  # 最終着用日
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 登録日時
```

#### バリデーション

- 全ての必須項目が入力されているか確認
- 用途ラベルが 1 つ以上選択されているか確認
- 写真が選択されているか確認

#### 保存処理

1. バリデーション実行
2. 新規の場合、UUID を生成して id に設定
3. 写真をローカルファイルシステムに保存（リサイズ・圧縮は任意）
4. SQLite データベースに保存
5. 保存成功後、一覧画面へリダイレクト

```python
# 保存例（Flask + SQLAlchemy）
from werkzeug.utils import secure_filename
import os
import uuid

@app.route('/closet/add', methods=['POST'])
def add_clothing():
    # バリデーション
    if 'photo' not in request.files:
        flash('写真を選択してください', 'error')
        return redirect(request.url)

    photo = request.files['photo']
    if photo.filename == '':
        flash('写真を選択してください', 'error')
        return redirect(request.url)

    # ファイル保存
    filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
    photo_path = os.path.join('static/uploads', filename)
    photo.save(photo_path)

    # DB保存
    purposes_str = ','.join(request.form.getlist('purposes'))
    new_clothing = Clothing(
        photo_path=photo_path,
        category=request.form['category'],
        subcategory=request.form['subcategory'],
        color=request.form['color'],
        purposes=purposes_str,
        last_worn_date=None
    )

    db.session.add(new_clothing)
    db.session.commit()

    return redirect(url_for('closet'))
```

---

## 4. 共通仕様

### ナビゲーション

- グローバルナビゲーション（下部タブバーまたはサイドメニュー）
  - ホーム（提案画面）
  - クローゼット一覧

### データ管理

#### ストレージ: SQLite（オンデバイス）

**選定理由**:

- ファイルベースのデータベースで、外部サーバー不要
- Python の標準ライブラリで利用可能
- 容量制限: 数 GB〜数十 GB（実質無制限）
- インデックスによる高速な検索が可能
- SQLAlchemy ORM により直感的なデータ操作が可能

**データベース構造**（SQLAlchemy 使用）:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fashion_app.db'
db = SQLAlchemy(app)

class Clothing(db.Model):
    __tablename__ = 'clothing'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_path = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    subcategory = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    purposes = db.Column(db.String(100), nullable=False)  # カンマ区切り
    last_worn_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    __tablename__ = 'settings'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
```

**主要な操作**:

```python
# 全件取得
all_clothes = Clothing.query.all()

# フィルタリング
tops = Clothing.query.filter_by(category='トップス').all()

# 用途ラベルで検索（部分一致）
school_clothes = Clothing.query.filter(Clothing.purposes.like('%学校%')).all()

# 最終着用日でフィルタ（2日以内を除外）
from datetime import datetime, timedelta
two_days_ago = datetime.now().date() - timedelta(days=2)
available_clothes = Clothing.query.filter(
    (Clothing.last_worn_date < two_days_ago) | (Clothing.last_worn_date == None)
).all()

# 設定の保存
setting = Settings.query.filter_by(key='defaultPlan').first()
if setting:
    setting.value = '学校'
else:
    setting = Settings(key='defaultPlan', value='学校')
    db.session.add(setting)
db.session.commit()

# 設定の取得
default_plan = Settings.query.filter_by(key='defaultPlan').first()
```

**写真の表示**:

```python
# Jinja2テンプレートで表示
# {{ url_for('static', filename=clothing.photo_path.replace('static/', '')) }}

# または、直接パスを使用
# <img src="{{ clothing.photo_path }}" alt="服の写真">
```

### 外部 API 連携

- **天気 API**: OpenWeatherMap API
- **必要な情報**:
  - ユーザーの地域設定（別途設定画面が必要）
  - API キーの管理（環境変数）
- **取得データ**: 現在の気温（℃）

### レスポンシブデザイン

- モバイルファーストで設計
- スマートフォン（320px〜）での利用を最優先
- タブレット、デスクトップでも適切に表示

### 技術スタック

- **Flask**: Python Web フレームワーク
- **Python**: プログラミング言語
- **Jinja2**: テンプレートエンジン（Flask 標準）
- **Tailwind CSS**: スタイリング
- **SQLite**: オンデバイスデータベース
- **SQLAlchemy**: ORM ライブラリ
- **OpenWeatherMap API**: 天気・気温情報取得
- **Werkzeug**: ファイルアップロード処理（Flask 標準）

### 必要なパッケージ

```bash
pip install flask flask-sqlalchemy requests python-dotenv
```

または requirements.txt を使用:

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
requests==2.31.0
python-dotenv==1.0.0
Pillow==10.1.0  # 画像処理（リサイズ等）が必要な場合
```

```bash
pip install -r requirements.txt
```
