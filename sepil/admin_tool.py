import sqlite3

def admin_menu():
    conn = sqlite3.connect('sepil.db')
    c = conn.cursor()
    while True:
        print("\n--- SEPIL ADMIN PANEL ---")
        print("1. Посмотреть РЕПОРТЫ")
        print("2. ЗАБАНИТЬ пользователя")
        print("3. Выход")
        choice = input(">> ")

        if choice == '1':
            reports = c.execute("SELECT * FROM reports").fetchall()
            for r in reports: print(f"[{r[0]}] От: {r[1]} на {r[2]} | Причина: {r[3]}")
        elif choice == '2':
            user = input("Кого забанить?: ")
            c.execute("UPDATE users SET status = 'banned' WHERE username = ?", (user,))
            conn.commit()
            print("Забанен.")
        elif choice == '3': break
    conn.close()

if __name__ == "__main__": admin_menu()