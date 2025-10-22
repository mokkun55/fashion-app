"""
ユーティリティ関数
"""
import requests
from datetime import datetime, timedelta
from flask import current_app
import random


def get_weather_info(city=None, latitude=None, longitude=None):
    """
    OpenWeatherMap APIから天気情報を取得
    
    Args:
        city: 都市名（Noneの場合は設定から取得）
        latitude: 緯度（位置情報がある場合）
        longitude: 経度（位置情報がある場合）
    
    Returns:
        dict: {
            'temperature': 気温(℃),
            'city': 都市名,
            'description': 天気の説明,
            'error': エラーメッセージ（エラー時のみ）
        }
    """
    api_key = current_app.config.get('OPENWEATHER_API_KEY')
    
    if not api_key:
        return {
            'temperature': None,
            'city': city or 'Tokyo',
            'description': 'APIキーが設定されていません',
            'error': True
        }
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'appid': api_key,
            'units': 'metric',  # 摂氏で取得
            'lang': 'ja'  # 日本語
        }
        
        # 位置情報がある場合は座標で検索、ない場合は都市名で検索
        if latitude and longitude:
            params['lat'] = latitude
            params['lon'] = longitude
        else:
            city = city or current_app.config.get('DEFAULT_CITY', 'Tokyo')
            params['q'] = city
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # 都市名を取得（位置情報の場合はAPIから取得した都市名を使用）
        if latitude and longitude:
            city_name = data['name']
        else:
            city_name = city
        
        return {
            'temperature': round(data['main']['temp'], 1),
            'city': city_name,
            'description': data['weather'][0]['description'],
            'error': False
        }
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Weather API error: {e}")
        return {
            'temperature': None,
            'city': city or 'Tokyo',
            'description': 'APIの接続に失敗しました',
            'error': True
        }


def get_clothing_recommendation(temperature):
    """
    気温に基づいて推奨される服の種類を返す
    
    Args:
        temperature: 気温(℃)
    
    Returns:
        dict: {
            'top_subcategory': トップスの中分類,
            'bottom_subcategory': ボトムスの中分類,
            'message': 補足メッセージ
        }
    """
    if temperature is None:
        return {
            'top_subcategory': None,
            'bottom_subcategory': None,
            'message': '気温情報を取得できませんでした'
        }
    
    if temperature >= 28:
        return {
            'top_subcategory': '半袖',
            'bottom_subcategory': '短め',
            'message': '暑い日です。涼しい服装がおすすめです。'
        }
    elif temperature >= 20:
        return {
            'top_subcategory': '長袖・薄手',
            'bottom_subcategory': '長め',
            'message': '過ごしやすい気温です。'
        }
    elif temperature >= 15:
        return {
            'top_subcategory': '長袖・厚手',
            'bottom_subcategory': '長め',
            'message': '少し肌寒いです。'
        }
    else:
        return {
            'top_subcategory': '長袖・厚手',
            'bottom_subcategory': '長め',
            'message': '寒い日です。アウターを羽織ることをおすすめします。'
        }


def generate_outfit_suggestions(clothes_list, purpose, temperature, count=3):
    """
    服のリストから条件に合うコーディネートを生成
    
    Args:
        clothes_list: 服のリスト（Clothingモデルのクエリ結果）
        purpose: 用途（"大学", "企業", "デート"）
        temperature: 気温(℃)
        count: 生成する提案数
    
    Returns:
        list: [{'top': Clothing, 'bottom': Clothing}, ...]
    """
    from datetime import date, timedelta
    
    # 気温に基づく推奨服種を取得
    recommendation = get_clothing_recommendation(temperature)
    
    # 条件でフィルタリング
    filtered_tops = []
    filtered_bottoms = []
    
    two_days_ago = date.today() - timedelta(days=2)
    
    for clothing in clothes_list:
        # 用途ラベルチェック
        purposes = clothing.get_purposes_list()
        if purpose not in purposes:
            continue
        
        # 最終着用日チェック（2日以内は除外）
        if clothing.last_worn_date and clothing.last_worn_date >= two_days_ago:
            continue
        
        # カテゴリと気温による絞り込み
        if clothing.category == 'トップス':
            if recommendation['top_subcategory'] and \
               clothing.subcategory == recommendation['top_subcategory']:
                filtered_tops.append(clothing)
        elif clothing.category == 'ボトムス':
            if recommendation['bottom_subcategory'] and \
               clothing.subcategory == recommendation['bottom_subcategory']:
                filtered_bottoms.append(clothing)
    
    # コーディネートを生成
    suggestions = []
    
    if not filtered_tops or not filtered_bottoms:
        return suggestions
    
    # ランダムに組み合わせて生成
    max_combinations = min(len(filtered_tops) * len(filtered_bottoms), count)
    
    # 全組み合わせを作成
    all_combinations = []
    for top in filtered_tops:
        for bottom in filtered_bottoms:
            all_combinations.append({'top': top, 'bottom': bottom})
    
    # ランダムにシャッフルして必要数取得
    random.shuffle(all_combinations)
    suggestions = all_combinations[:count]
    
    return suggestions


def get_outfit_color_match_score(top_color, bottom_color):
    """
    トップスとボトムスの色の相性スコアを返す（将来的な拡張用）
    
    Args:
        top_color: トップスの色
        bottom_color: ボトムスの色
    
    Returns:
        int: 相性スコア（0-100）
    """
    # 基本的な色の相性ルール
    good_combinations = [
        ('黒', '白'), ('白', '黒'),
        ('紺', 'ベージュ'), ('ベージュ', '紺'),
        ('グレー', '黒'), ('黒', 'グレー'),
        ('白', '青'), ('青', '白'),
    ]
    
    if (top_color, bottom_color) in good_combinations:
        return 90
    
    # 同系色は避ける
    if top_color == bottom_color and top_color not in ['黒', '白', 'グレー']:
        return 30
    
    # デフォルト
    return 50

