import flet as ft
import sqlite3

def main(page: ft.Page):
    # アプリの基本設定
    page.title = "アパホテル宿泊価格分析ダッシュボード"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20

    # -----------------------------------------
    # 1. データベースからホテルデータを取得する関数
    # -----------------------------------------
    def get_data_from_db(budget=None):
        # 自分の作成したDBに接続
        conn = sqlite3.connect('hotel_analysis.db')
        cur = conn.cursor()
        
        if budget:
            # 予算以下のホテルを抽出（動的な出力要件）
            query = "SELECT target_date, name, price FROM hotel_prices WHERE price <= ? ORDER BY price ASC"
            cur.execute(query, (budget,))
        else:
            # 指定がない場合は全件表示（最新100件）
            cur.execute("SELECT target_date, name, price FROM hotel_prices LIMIT 100")
            
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
                        ft.DataCell(ft.Text(row[0], size=12)),                # 対象日程
                        ft.DataCell(ft.Text(row[1], size=12, weight="bold")), # ホテル名
                        ft.DataCell(ft.Text(f"{row[2]:,}円", color="blue")),  # 宿泊価格
                    ]
                )
            )
        return rows

    # -----------------------------------------
    # 3. 画面パーツ（UI）の作成
    # -----------------------------------------
    title_text = ft.Text("イベント期間の宿泊費分析ダッシュボード", size=24, weight="bold", color="blue")
    status_text = ft.Text("データを読み込み中...", color="grey")

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("対象日程")),
            ft.DataColumn(ft.Text("ホテル名")),
            ft.DataColumn(ft.Text("宿泊価格", numeric=True)),
        ],
        rows=[],
        border=ft.border.all(1, "grey"),
        vertical_lines=ft.border.BorderSide(1, "grey"),
        heading_row_color=ft.colors.BLUE_GREY_50,
        expand=True
    )

    # -----------------------------------------
    # 4. イベント処理（予算検索）
    # -----------------------------------------
    def search_click(e):
        try:
            # 予算が空の場合は非常に大きい数値を設定
            budget = int(search_field.value) if search_field.value else 999999
            results = get_data_from_db(budget)
            data_table.rows = create_table_rows(results)
            
            if len(results) == 0:
                status_text.value = f"{budget:,}円以下のホテルは見つかりませんでした。"
                status_text.color = "red"
            else:
                status_text.value = f"予算内（{budget:,}円以下）の検索結果: {len(results)} 件"
                status_text.color = "black"
        except ValueError:
            status_text.value = "数字を入力してください。"
            status_text.color = "red"
            
        page.update()

    search_field = ft.TextField(
        label="予算上限を入力してください（例: 15000）", 
        width=400, 
        prefix_icon=ft.icons.MONETIZATION_ON,
        on_submit=search_click
    )
    search_button = ft.ElevatedButton(content=ft.Text("検索"), on_click=search_click)

    # 初期処理
    try:
        initial_data = get_data_from_db()
        data_table.rows = create_table_rows(initial_data)
        status_text.value = "DBから最新データを取得しました。"
    except sqlite3.OperationalError:
        status_text.value = "エラー：先に『最終課題.ipynb』を実行してデータを溜めてください。"
        status_text.color = "red"

    # レイアウト
    page.add(
        ft.Column([
            title_text,
            ft.Divider(),
            ft.Row([search_field, search_button], alignment="center"),
            status_text,
            ft.Container(
                content=ft.Column([data_table], scroll=ft.ScrollMode.AUTO),
                height=500,
                border=ft.border.all(1, "grey50"),
                border_radius=10,
                padding=10
            )
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)