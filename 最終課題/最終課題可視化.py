import sqlite3
import flet as ft  

class HotelApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.budget_input = ft.TextField(label="予算を入力 (円)", value="10000", width=200)
        self.result_list = ft.ListView(expand=True, spacing=10, padding=20)
        self.controls = [
            ft.Text(" 宿泊費分析 ", size=20, weight="bold"),
            ft.Row([self.budget_input, ft.ElevatedButton("検索", on_click=self.search)]),
            self.result_list
        ]

    def search(self, e):
        self.result_list.controls.clear()
        budget = int(self.budget_input.value)
        
        conn = sqlite3.connect('hotel_analysis.db')
        cursor = conn.cursor()
        # 予算以下のホテルをDBから抽出（動的な出力要件）
        cursor.execute('SELECT * FROM hotel_prices WHERE price <= ? ORDER BY price ASC', (budget,))
        
        for row in cursor.fetchall():
            self.result_list.controls.append(
                ft.ListTile(
                    title=ft.Text(f"【{row[0]}】 {row[1]}"),
                    subtitle=ft.Text(f"価格: {row[2]:,}円"),
                    leading=ft.Icon(ft.Icons.HOTEL)
                )
            )
        conn.close()
        self.update()

def main(page: ft.Page):
    page.title = "最終課題：イベント宿泊費分析"
    # 最初にデータを取得・保存
    # fetch_and_save() 
    page.add(HotelApp())

if __name__ == "__main__":
    ft.app(target=main)