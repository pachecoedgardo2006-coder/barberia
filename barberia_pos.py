import customtkinter as ctk
import sqlite3
from tkinter import messagebox, ttk
from datetime import datetime
import os

# --- CONFIGURACIÓN GLOBAL ---
BARBEROS = ["Edward","Invitado"]
COLOR_CAJA = "#2fa572"
COLOR_BARBERO = "#3b8ed0"
COLOR_LOCAL = "#e5a823"

def create_db():
    conn = sqlite3.connect("barberia.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            barber_name TEXT NOT NULL,
            price REAL NOT NULL,
            comision_barbero REAL NOT NULL,
            comision_empresa REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- FUNCIONES DE LÓGICA ---
def save_sale_to_db(name, barber, price):
    c_barbero = price * 0.60
    c_empresa = price * 0.40
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Fecha local exacta
    try:
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO sales (service_name, barber_name, price, comision_barbero, comision_empresa, date) 
                          VALUES (?, ?, ?, ?, ?, ?)''', (name, barber, price, c_barbero, c_empresa, fecha_actual))
        conn.commit()
        conn.close()
        return True
    except: return False

def delete_sale(sale_id):
    try:
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        conn.commit()
        conn.close()
        return True
    except: return False

# --- VENTANA DE HISTORIAL Y CIERRE ---
# --- VENTANA DE HISTORIAL Y CIERRE ---
def open_history_window():
    history_win = ctk.CTkToplevel()
    history_win.title("Sistema de Cierre de Caja")
    history_win.geometry("1100x750")
    # Se eliminó 'topmost' para que los mensajes de confirmación no queden detrás
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    # --- FILTROS ---
    filter_frame = ctk.CTkFrame(history_win, fg_color="#1e1e1e")
    filter_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(filter_frame, text="Desde:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    entry_desde = ctk.CTkEntry(filter_frame, width=110)
    entry_desde.insert(0, fecha_hoy)
    entry_desde.pack(side="left", padx=5)

    ctk.CTkLabel(filter_frame, text="Hasta:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    entry_hasta = ctk.CTkEntry(filter_frame, width=110)
    entry_hasta.insert(0, fecha_hoy)
    entry_hasta.pack(side="left", padx=5)

    filtro_var = ctk.StringVar(value="Todos")
    ctk.CTkOptionMenu(filter_frame, values=["Todos"] + BARBEROS, variable=filtro_var, width=140).pack(side="right", padx=10)
    ctk.CTkLabel(filter_frame, text="Barbero:").pack(side="right")

    # --- TABLA ---
    table_frame = ctk.CTkFrame(history_win)
    table_frame.pack(expand=True, fill="both", padx=20, pady=10)

    columns = ("id", "servicio", "barbero", "total", "com_barbero", "empresa", "hora")
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30)
    style.configure("Treeview.Heading", background="#1e1e1e", foreground="white", font=("Arial", 11, "bold"))

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    for col, txt in zip(columns, ["ID", "SERVICIO", "BARBERO", "TOTAL $", "PAGO 60%", "LOCAL 40%", "HORA"]):
        tree.heading(col, text=txt)
        tree.column(col, width=130, anchor="center")

    tree.pack(side="left", expand=True, fill="both")
    scrollbar.pack(side="right", fill="y")

    # --- PANEL DE RESULTADOS ---
    resumen_frame = ctk.CTkFrame(history_win)
    resumen_frame.pack(fill="x", padx=20, pady=10)

    lbl_total = ctk.CTkLabel(resumen_frame, text="", font=("Arial", 18, "bold"), text_color=COLOR_CAJA)
    lbl_total.pack(side="left", expand=True)
    lbl_barbero = ctk.CTkLabel(resumen_frame, text="", font=("Arial", 18, "bold"), text_color=COLOR_BARBERO)
    lbl_barbero.pack(side="left", expand=True)
    lbl_local = ctk.CTkLabel(resumen_frame, text="", font=("Arial", 18, "bold"), text_color=COLOR_LOCAL)
    lbl_local.pack(side="left", expand=True)

    def actualizar_tabla(*args):
        for item in tree.get_children(): tree.delete(item)
        f_ini, f_fin, barber = entry_desde.get(), entry_hasta.get(), filtro_var.get()
        
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        query = "SELECT * FROM sales WHERE date(date) BETWEEN date(?) AND date(?)"
        params = [f_ini, f_fin]
        if barber != "Todos":
            query += " AND barber_name = ?"
            params.append(barber)
            
        cursor.execute(query, params)
        t_b = t_bar = t_loc = 0
        for row in cursor.fetchall():
            t_b += row[3]; t_bar += row[4]; t_loc += row[5]
            hora = row[6].split(" ")[1] if " " in row[6] else "00:00"
            tree.insert("", "end", values=(row[0], row[1], row[2], f"${row[3]:,.0f}", f"${row[4]:,.0f}", f"${row[5]:,.0f}", hora))
        conn.close()
        
        lbl_total.configure(text=f"Total Rango\n${t_b:,.0f}")
        lbl_barbero.configure(text=f"Comisión {barber}\n${t_bar:,.0f}")
        lbl_local.configure(text=f"Ganancia Local\n${t_loc:,.0f}")

    ctk.CTkButton(filter_frame, text="🔍 Filtrar", command=actualizar_tabla, width=100, fg_color=COLOR_CAJA).pack(side="left", padx=20)

    # --- ACCIONES ---
    def handle_delete():
        selected = tree.selection()
        if not selected:
            return messagebox.showwarning("Atención", "Selecciona una venta", parent=history_win)
        
        item_id = tree.item(selected)['values'][0]
        # 'parent=history_win' asegura que el mensaje salga sobre esta ventana
        if messagebox.askyesno("Confirmar", f"¿Borrar la venta #{item_id}?", parent=history_win):
            if delete_sale(item_id):
                actualizar_tabla()
                messagebox.showinfo("Éxito", "Venta eliminada", parent=history_win)

    def export_report():
        filtro = filtro_var.get()
        filename = f"Reporte_{filtro}_{fecha_hoy}.txt"
        with open(filename, "w") as f:
            f.write(f"REPORTE: {fecha_hoy}\n{lbl_total.cget('text')}\n{lbl_barbero.cget('text')}\n{lbl_local.cget('text')}")
        messagebox.showinfo("Éxito", f"Guardado como {filename}", parent=history_win)

    actions_frame = ctk.CTkFrame(history_win, fg_color="transparent")
    actions_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkButton(actions_frame, text="🗑 Eliminar Venta", fg_color="#922b21", command=handle_delete).pack(side="left", padx=10)
    ctk.CTkButton(actions_frame, text="📄 Exportar (.txt)", fg_color="#1e8449", command=export_report).pack(side="right", padx=10)

    filtro_var.trace_add("write", actualizar_tabla)
    actualizar_tabla()

# --- VENTANA PRINCIPAL ---
# --- VENTANA PRINCIPAL CORREGIDA ---
def main_window():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("BarberShop Professional POS")
    root.geometry("500x780") # Un poco más de altura por seguridad

    ctk.CTkLabel(root, text="💈 TAJAMARES BARBER SHOP 💈", font=("Arial", 26, "bold")).pack(pady=20)
    
    # Selector Barbero
    select_frame = ctk.CTkFrame(root, fg_color="transparent")
    select_frame.pack(pady=5)
    ctk.CTkLabel(select_frame, text="BARBERO DE TURNO:", font=("Arial", 12, "bold")).pack()
    barber_selector = ctk.CTkOptionMenu(select_frame, values=BARBEROS, width=300, height=40, font=("Arial", 14))
    barber_selector.pack(pady=5)

    servicios = {
        "✂️ Corte Caballero": 30000,
        "💇 Corte Niño": 25000,
        "🧔 Barba Premium": 15000,
        "Barba + Tinte": 22000,
        "🔥 Combo Corte + Barbaba": 40000,
        "✏️ Cejas / Marcación": 15000,
    }

    def process_sale(n, p):
        barbero = barber_selector.get()
        if save_sale_to_db(n, barbero, p):
            messagebox.showinfo("Venta", f"{n} registrado a {barbero}")

    # --- CAMBIO CLAVE AQUÍ: expand=False ---
    frame_btns = ctk.CTkFrame(root, fg_color="#2b2b2b", corner_radius=15)
    frame_btns.pack(pady=10, padx=30, fill="both", expand=False) 

    ctk.CTkLabel(frame_btns, text="SERVICIOS", font=("Arial", 14, "bold"), text_color="#aaaaaa").pack(pady=5)

    for n, p in servicios.items():
        btn = ctk.CTkButton(frame_btns, text=f"{n} (${p:,.0f})", # Texto en una línea para ahorrar espacio
                            command=lambda n=n, p=p: process_sale(n, p),
                            height=45, font=("Arial", 13, "bold"),
                            fg_color="#3b3b3b", hover_color="#4b4b4b")
        btn.pack(pady=4, padx=20, fill="x")

    # --- ESTE BOTÓN AHORA TIENE PRIORIDAD ---
    btn_reporte = ctk.CTkButton(root, text="📊 VER REPORTES Y CIERRE DE CAJA", 
                  command=open_history_window, 
                  fg_color=COLOR_BARBERO, hover_color="#2e6da4",
                  height=60, font=("Arial", 15, "bold"))
    
    # Usamos un pady mayor para separarlo de los botones de arriba
    btn_reporte.pack(side="bottom", pady=30, padx=30, fill="x")

    root.mainloop()

if __name__ == "__main__":
    create_db()
    main_window()