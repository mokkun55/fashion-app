"""
画像処理機能 - 色検出と輪郭検出による服の属性自動判定
"""
import cv2
import numpy as np
from PIL import Image
import os
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import KMeans


class ClothingImageProcessor:
    """服の画像を処理して属性を自動判定するクラス"""
    
    def __init__(self):
        # 色の名前とHSV範囲のマッピング
        self.color_ranges = {
            '黒': [(0, 0, 0), (180, 255, 50)],
            '白': [(0, 0, 200), (180, 30, 255)],
            'グレー': [(0, 0, 50), (180, 30, 200)],
            '赤': [(0, 100, 100), (10, 255, 255), (170, 100, 100), (180, 255, 255)],
            'ピンク': [(140, 50, 100), (180, 255, 255)],
            'オレンジ': [(10, 100, 100), (25, 255, 255)],
            '黄色': [(25, 100, 100), (35, 255, 255)],
            '緑': [(35, 100, 100), (85, 255, 255)],
            '青': [(100, 100, 100), (130, 255, 255)],
            '紫': [(130, 100, 100), (160, 255, 255)],
            '茶色': [(10, 100, 20), (20, 255, 200)],
            'ベージュ': [(20, 30, 150), (30, 100, 255)]
        }
        
        # 色の日本語名
        self.color_names = {
            '黒': '黒', '白': '白', 'グレー': 'グレー', '赤': '赤', 'ピンク': 'ピンク',
            'オレンジ': 'オレンジ', '黄色': '黄色', '緑': '緑', '青': '青', '紫': '紫',
            '茶色': '茶色', 'ベージュ': 'ベージュ'
        }
    
    def process_image(self, image_path: str) -> Dict:
        """
        画像を処理して服の属性を自動判定する
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            判定結果の辞書
        """
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                return {'error': '画像を読み込めませんでした'}
            
            # 画像の前処理
            processed_image = self._preprocess_image(image)
            
            # 色検出
            dominant_colors = self._detect_colors(processed_image)
            
            # 輪郭検出による形状分析
            shape_analysis = self._analyze_shape(processed_image)
            
            # サイズ感の推定
            size_estimation = self._estimate_size(processed_image, shape_analysis)
            
            # カテゴリの推定
            category_estimation = self._estimate_category(shape_analysis, size_estimation)
            
            return {
                'dominant_colors': dominant_colors,
                'shape_analysis': shape_analysis,
                'size_estimation': size_estimation,
                'category_estimation': category_estimation,
                'confidence': self._calculate_confidence(dominant_colors, shape_analysis)
            }
            
        except Exception as e:
            return {'error': f'画像処理中にエラーが発生しました: {str(e)}'}
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """画像の前処理"""
        # リサイズ（処理速度向上のため）
        height, width = image.shape[:2]
        if width > 800:
            scale = 800 / width
            new_width = 800
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # ノイズ除去
        image = cv2.medianBlur(image, 5)
        
        return image
    
    def _detect_colors(self, image: np.ndarray) -> List[Dict]:
        """主要な色を検出する"""
        # BGRからHSVに変換
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 画像をリシェイプしてK-meansクラスタリング用に準備
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        # K-meansクラスタリングで主要色を抽出
        k = 5  # 主要色の数
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 各クラスターのピクセル数を計算
        unique, counts = np.unique(labels, return_counts=True)
        
        # 色の割合と色名を取得
        colors = []
        for i, (center, count) in enumerate(zip(centers, counts)):
            percentage = (count / len(data)) * 100
            if percentage > 5:  # 5%以上の色のみを対象
                bgr_color = center.astype(np.uint8)
                color_name = self._identify_color(bgr_color)
                colors.append({
                    'color': color_name,
                    'percentage': round(percentage, 1),
                    'bgr': bgr_color.tolist()
                })
        
        # 割合でソート
        colors.sort(key=lambda x: x['percentage'], reverse=True)
        
        return colors
    
    def _identify_color(self, bgr_color: np.ndarray) -> str:
        """BGR色から色名を特定する"""
        # BGRからHSVに変換
        bgr_array = np.uint8([[bgr_color]])
        hsv_color = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)[0][0]
        
        # 各色の範囲と比較
        for color_name, ranges in self.color_ranges.items():
            if self._is_color_in_range(hsv_color, ranges):
                return self.color_names.get(color_name, 'その他')
        
        return 'その他'
    
    def _is_color_in_range(self, hsv_color: np.ndarray, ranges: List[Tuple]) -> bool:
        """HSV色が指定された範囲内かチェック"""
        h, s, v = hsv_color
        
        # 複数の範囲がある場合（例：赤）
        if len(ranges) == 4:  # 2つの範囲
            range1_lower, range1_upper, range2_lower, range2_upper = ranges
            return (range1_lower[0] <= h <= range1_upper[0] and 
                    range1_lower[1] <= s <= range1_upper[1] and 
                    range1_lower[2] <= v <= range1_upper[2]) or \
                   (range2_lower[0] <= h <= range2_upper[0] and 
                    range2_lower[1] <= s <= range2_upper[1] and 
                    range2_lower[2] <= v <= range2_upper[2])
        else:  # 1つの範囲
            lower, upper = ranges
            return (lower[0] <= h <= upper[0] and 
                    lower[1] <= s <= upper[1] and 
                    lower[2] <= v <= upper[2])
    
    def _analyze_shape(self, image: np.ndarray) -> Dict:
        """輪郭検出による形状分析"""
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # エッジ検出
        edges = cv2.Canny(gray, 50, 150)
        
        # 輪郭検出
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'error': '輪郭を検出できませんでした'}
        
        # 最大の輪郭を取得
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 輪郭の特徴を計算
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # アスペクト比を計算
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = w / h if h > 0 else 0
        
        # 円形度を計算
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        return {
            'area': area,
            'perimeter': perimeter,
            'aspect_ratio': aspect_ratio,
            'circularity': circularity,
            'width': w,
            'height': h,
            'bounding_box': (x, y, w, h)
        }
    
    def _estimate_size(self, image: np.ndarray, shape_analysis: Dict) -> Dict:
        """サイズ感を推定する"""
        if 'error' in shape_analysis:
            return {'error': '形状分析に失敗しました'}
        
        aspect_ratio = shape_analysis['aspect_ratio']
        area = shape_analysis['area']
        total_pixels = image.shape[0] * image.shape[1]
        area_ratio = area / total_pixels
        
        # アスペクト比に基づく判定
        if aspect_ratio > 1.5:
            size_type = '横長'
        elif aspect_ratio < 0.7:
            size_type = '縦長'
        else:
            size_type = '正方形に近い'
        
        # 面積に基づくサイズ感
        if area_ratio > 0.7:
            size_level = '大きめ'
        elif area_ratio > 0.3:
            size_level = '普通'
        else:
            size_level = '小さめ'
        
        return {
            'size_type': size_type,
            'size_level': size_level,
            'area_ratio': area_ratio
        }
    
    def _estimate_category(self, shape_analysis: Dict, size_estimation: Dict) -> Dict:
        """カテゴリを推定する"""
        if 'error' in shape_analysis or 'error' in size_estimation:
            return {'error': '分析に失敗しました'}
        
        aspect_ratio = shape_analysis['aspect_ratio']
        size_type = size_estimation['size_type']
        
        # アスペクト比に基づくカテゴリ推定
        if aspect_ratio > 1.3:
            # 横長 → ボトムスの可能性が高い
            category = 'ボトムス'
            subcategory = '長め' if aspect_ratio > 2.0 else '短め'
        elif aspect_ratio < 0.8:
            # 縦長 → トップスの可能性が高い
            category = 'トップス'
            # サイズ感で細分化
            if size_estimation['size_level'] == '大きめ':
                subcategory = '長袖・厚手'
            else:
                subcategory = '半袖'
        else:
            # 正方形に近い → 判断が困難
            category = '不明'
            subcategory = '不明'
        
        return {
            'category': category,
            'subcategory': subcategory,
            'confidence': self._calculate_category_confidence(aspect_ratio, size_type)
        }
    
    def _calculate_category_confidence(self, aspect_ratio: float, size_type: str) -> float:
        """カテゴリ推定の信頼度を計算"""
        confidence = 0.5  # ベース信頼度
        
        # アスペクト比による調整
        if aspect_ratio > 1.5 or aspect_ratio < 0.7:
            confidence += 0.3  # 明確な形状
        elif 1.0 <= aspect_ratio <= 1.3:
            confidence -= 0.2  # 判断が困難
        
        return min(max(confidence, 0.0), 1.0)
    
    def _calculate_confidence(self, colors: List[Dict], shape_analysis: Dict) -> float:
        """全体的な信頼度を計算"""
        if 'error' in shape_analysis:
            return 0.0
        
        # 色検出の信頼度
        color_confidence = min(len(colors) * 0.2, 1.0)
        
        # 形状分析の信頼度
        shape_confidence = 0.8 if shape_analysis['area'] > 1000 else 0.5
        
        # 全体の信頼度
        overall_confidence = (color_confidence + shape_confidence) / 2
        
        return round(overall_confidence, 2)


def process_clothing_image(image_path: str) -> Dict:
    """
    服の画像を処理する便利関数
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        処理結果の辞書
    """
    processor = ClothingImageProcessor()
    return processor.process_image(image_path)