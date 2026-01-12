import requests
import flet as ft
import sqlite3 # SQLiteを使用するために追加

FORECAST_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"

# 47都道府県リスト
PREFS = {
    "北海道地方": {"016000": "札幌"},
    "東北地方": {"020000": "青森", "030000": "岩手", "040000": "宮城", "050000": "秋田", "060000": "山形", "070000": "福島"},
    "関東甲信地方": {"080000": "茨城", "090000": "栃木", "100000": "群馬", "110000": "埼玉", "120000": "千葉", "130000": "東京", "140000": "神奈川", "190000": "山梨", "200000": "長野"},
    "北陸・東海地方": {"150000": "新潟", "160000": "富山", "170000": "石川", "180000": "福井", "210000": "岐阜", "220000": "静岡", "230000": "愛知", "240000": "三重"},
    "近畿地方": {"250000": "滋賀", "260000": "京都", "270000": "大阪", "280000": "兵庫", "290000": "奈良", "300000": "和歌山"},
    "中国・四国地方": {"310000": "鳥取", "320000": "島根", "330000": "岡山", "340000": "広島", "350000": "山口", "360000": "徳島", "370000": "香川", "380000": "愛媛", "390000": "高知"},
    "九州・沖縄地方": {"400000": "福岡", "410000": "佐賀", "420000": "長崎", "430000": "熊本", "440000": "大分", "450000": "宮崎", "460100": "鹿児島", "471000": "沖縄"}
}

# --- 🗄 データベース関連の関数 ---

def init_db():
    """データベースとテーブルの初期化"""
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    # 日付と地域コードを組み合わせてプライマリーキー（一意）にする設計
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            date TEXT,
            area_code TEXT,
            area_name TEXT,
            weather TEXT,
            temp_min TEXT,
            temp_max TEXT,
            PRIMARY KEY (date, area_code)
        )
    ''')
    conn.commit()
    return conn

def save_to_db(forecast_list):
    """取得したデータを一括でDBに保存"""
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR REPLACE INTO forecasts (date, area_code, area_name, weather, temp_min, temp_max)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', forecast_list)
    conn.commit()
    conn.close()

def get_from_db(area_code):
    """DBから特定の地域の予報を取得"""
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, weather, temp_min, temp_max FROM forecasts WHERE area_code = ? ORDER BY date ASC', (area_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- 🌤 アプリのロジック ---

def get_forecast_data(area_code):
    """APIからデータを取得"""
    response = requests.get(f"{FORECAST_BASE_URL}{area_code}.json")
    return response.json()

def get_weather_icon(weather_text):
    """天気に合わせたアイコンを取得"""
    if "晴" in weather_text: return ft.Icons.WB_SUNNY
    elif "雨" in weather_text: return ft.Icons.UMBRELLA
    elif "曇" in weather_text or "くもり" in weather_text: return ft.Icons.CLOUD
    elif "雪" in weather_text: return ft.Icons.AC_UNIT
    return ft.Icons.HELP

def create_forecast_card(date_str, weather_text, temp_min, temp_max):
    """予報カードのデザイン"""
    return ft.Card(
        elevation=4,
        content=ft.Container(
            content=ft.Column([
                ft.Text(date_str[:10], size=14, weight="bold", color="blue_grey_400"),
                ft.Icon(get_weather_icon(weather_text), size=50, color="orange_400"),
                ft.Text(weather_text, size=14, weight="bold", text_align="center"),
                ft.Row([
                    ft.Text(f"{temp_min}°C", color="blue_600", size=18, weight="bold"),
                    ft.Text("/", size=18, color="grey"),
                    ft.Text(f"{temp_max}°C", color="red_600", size=18, weight="bold"),
                ], alignment="center")
            ], horizontal_alignment="center", spacing=10),
            padding=20, width=170
        )
    )

def main(page: ft.Page):
    # DB初期化
    init_db()

    page.title = "気象庁 天気予報アプリ (SQLite版)"
    page.bgcolor = "#CFD8DC"
    page.padding = 0

    forecast_display = ft.Row(wrap=True, spacing=20, scroll="auto", expand=True)
    title_text = ft.Text("地域を選択してください", size=24, weight="bold", color="white")
    
    current_tile = [None]

    def on_area_select(e, area_code, area_name):
        if current_tile[0]:
            current_tile[0].selected = False
            current_tile[0].update()

        e.control.selected = True
        e.control.update()
        current_tile[0] = e.control

        title_text.value = f"{area_name}の天気予報"
        
        try:
            # 1. まずAPIから最新データを取得
            data = get_forecast_data(area_code)
            time_series = data[0]['timeSeries']
            dates = time_series[0]['timeDefines']
            weathers = time_series[0]['areas'][0]['weathers']
            temps = []
            for s in time_series:
                if 'temps' in s['areas'][0]:
                    temps = s['areas'][0]['temps']
                    break
            
            # 2. データをDB保存用に整形
            forecast_list = []
            for i in range(len(weathers)):
                t_min = temps[i*2] if len(temps) > i*2 else "-"
                t_max = temps[i*2+1] if len(temps) > i*2 else "-"
                # (date, area_code, area_name, weather, temp_min, temp_max)
                forecast_list.append((dates[i][:10], area_code, area_name, weathers[i], t_min, t_max))
            
            # 3. DBへ保存（INSERT OR REPLACE）
            save_to_db(forecast_list)

            # 4. 表示のために「あえてDBから」読み出す（移行の証明）
            db_data = get_from_db(area_code)
            
            new_cards = []
            for row in db_data:
                # row[0]=date, row[1]=weather, row[2]=temp_min, row[3]=temp_max
                new_cards.append(create_forecast_card(row[0], row[1], row[2], row[3]))
            
            forecast_display.controls = new_cards
        except Exception as ex:
            print(ex)
            forecast_display.controls = [ft.Text("読み込み失敗", color="red")]
        
        page.update()

    # サイドバーのリスト作成
    sidebar_content = []
    for region, areas in PREFS.items():
        sidebar_content.append(
            ft.Container(content=ft.Text(region, color="white60", weight="bold"), padding=10)
        )
        for code, name in areas.items():
            tile = ft.ListTile(
                title=ft.Text(name, color="white"),
                subtitle=ft.Text(code, color="white38", size=10),
                selected_color=ft.Colors.YELLOW_ACCENT,
                selected_tile_color=ft.Colors.WHITE10,
                on_click=lambda e, c=code, n=name: on_area_select(e, c, n),
            )
            sidebar_content.append(tile)

    sidebar = ft.Container(
        content=ft.Column(sidebar_content, scroll="auto", spacing=0),
        width=240, bgcolor="#37474F", padding=10
    )

    header = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="white"), title_text], alignment="start"),
        bgcolor="#303F9F", padding=20
    )

    main_view = ft.Column([
        header,
        ft.Container(content=forecast_display, padding=30, expand=True)
    ], expand=True)

    page.add(ft.Row([sidebar, main_view], expand=True, spacing=0))

if __name__ == "__main__":
    ft.app(target=main)