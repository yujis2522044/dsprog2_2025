import flet as ft
import sqlite3

def main(page: ft.Page):
    # アプリの基本設定
    page.title = "物件データ検索アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20

    # -----------------------------------------
    # 1. データベースからデータを取得する関数
    # -----------------------------------------
    def get_data_from_db(keyword=""):
        conn = sqlite3.connect('最終課題.db')
        cur = conn.cursor()
        
        if keyword:
            query = """
                SELECT name, station, price, age, floor_plan 
                FROM properties 
                WHERE station LIKE ? OR name LIKE ?
            """
            cur.execute(query, (f'%{keyword}%', f'%{keyword}%'))
        else:
            cur.execute("SELECT name, station, price, age, floor_plan FROM properties LIMIT 100")
            
        rows = cur.fetchall()
        conn.close()
        return rows

    # -----------------------------------------
    # 2. データを画面の「表」に変換する関数
    # -----------------------------------------
    def create_table_rows(data):
        rows = []
        for row in data:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(row[0], size=12, weight="bold")), # 物件名
                        ft.DataCell(ft.Text(row[1], size=12)),                # 駅
                        ft.DataCell(ft.Text(f"{row[2]:,}円")),                 # 家賃
                        ft.DataCell(ft.Text(f"築{row[3]}年")),                # 築年数
                        ft.DataCell(ft.Text(row[4])),                         # 間取り
                    ]
                )
            )
        return rows

    # -----------------------------------------
    # 3. 画面パーツ（UI）の作成
    # -----------------------------------------
    title_text = ft.Text("物件データ分析ダッシュボード", size=24, weight="bold", color=ft.Colors.TEAL)
    status_text = ft.Text("データを読み込み中...", color=ft.Colors.GREY)

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("物件名")),
            ft.DataColumn(ft.Text("最寄駅")),
            ft.DataColumn(ft.Text("家賃"), numeric=True),
            ft.DataColumn(ft.Text("築年数"), numeric=True),
            ft.DataColumn(ft.Text("間取り")),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY),
        heading_row_color=ft.Colors.BLUE_GREY_50, # 大文字のColorsに修正
        expand=True
    )

    # -----------------------------------------
    # 4. イベント処理（検索ボタン）
    # -----------------------------------------
    def search_click(e):
        keyword = search_field.value
        results = get_data_from_db(keyword)
        data_table.rows = create_table_rows(results)
        
        if len(results) == 0:
            status_text.value = f"「{keyword}」に一致するデータは見つかりませんでした。"
            status_text.color = ft.Colors.RED
        else:
            status_text.value = f"検索結果: {len(results)} 件"
            status_text.color = ft.Colors.BLACK
            
        page.update()

    search_field = ft.TextField(
        label="駅名や物件名で検索", 
        width=400, 
        prefix_icon=ft.Icons.SEARCH,
        on_submit=search_click
    )
    search_button = ft.ElevatedButton(text="検索", on_click=search_click)

    # 初期処理
    try:
        initial_data = get_data_from_db()
        data_table.rows = create_table_rows(initial_data)
        status_text.value = f"全データ表示中（最新{len(initial_data)}件）"
    except sqlite3.OperationalError:
        status_text.value = "エラー：データベースが見つからないか空です。"
        status_text.color = ft.Colors.RED

    page.add(
        ft.Column([
            title_text,
            ft.Divider(),
            ft.Row([search_field, search_button], alignment=ft.MainAxisAlignment.CENTER),
            status_text,
            ft.Container(
                content=ft.Column([data_table], scroll=ft.ScrollMode.AUTO),
                height=500,
                border=ft.border.all(1, ft.Colors.GREY_50),
                border_radius=10,
                padding=10
            )
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)