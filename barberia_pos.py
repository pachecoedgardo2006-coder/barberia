import customtkinter as ctk
import sqlite3
from tkinter import messagebox, ttk
from datetime import datetime
import os


   # Nueva configuración de precios y repartición
SERVICIOS_CONFIG = {
        "Corte Caballero": {
            "precio": 30000, "barbero": 15000, "lavado": 2000, "local": 13000
        },
        "Corte de Niño": {
            "precio": 25000, "barbero": 12000, "lavado": 2000, "local": 11000
        },
        "Barba + Tinte": {
            "precio": 30000, "barbero": 10000, "lavado": 0, "local": 20000
        },
        "Barba Premium": {
            "precio": 15000, "barbero": 5000, "lavado": 0, "local": 10000
        },
        "Combo Corte + Barba": {
            "precio": 40000, "barbero": 18000, "lavado": 2000, "local": 20000
        },
        "Cejas / Marcación": {
            "precio": 15000, "barbero": 5000, "lavado": 0, "local": 10000
        },
        "Combo Barba Premium + Cejas": {
            "precio": 27000, "barbero": 12000, "lavado": 0, "local": 15000
        },
        "Combo Corte Niño + Diseño": {
            "precio": 30000, "barbero": 15000, "lavado": 2000, "local": 13000
        }
    }

# --- CONFIGURACIÓN GLOBAL ---
BARBEROS = ["Edward","Invitado"]
COLOR_CAJA = "#535353"
COLOR_BARBERO = "#3b8ed0"
COLOR_LOCAL = "#e5a823"

def create_db():
    conn = sqlite3.connect("barberia.db")
    cursor = conn.cursor()
    # Creamos la tabla si no existe con la estructura completa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            barber_name TEXT NOT NULL,
            price REAL NOT NULL,
            comision_barbero REAL NOT NULL,
            comision_empresa REAL NOT NULL,
            lavado_cabezal REAL DEFAULT 0,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT DEFAULT '',
            cliente_documento TEXT DEFAULT '', 
            ticket_text TEXT DEFAULT '' 
        )
    ''')
    
    # Truco de seguridad: Verificamos si las columnas nuevas existen 
    # (por si vienes de una versión muy vieja del script)
    cursor.execute("PRAGMA table_info(sales)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'cliente_documento' not in columns:
        cursor.execute('ALTER TABLE sales ADD COLUMN cliente_documento TEXT DEFAULT ""')
    if 'ticket_text' not in columns:
        cursor.execute('ALTER TABLE sales ADD COLUMN ticket_text TEXT DEFAULT ""')
        
    conn.commit()
    conn.close()

# --- FUNCIONES DE LÓGICA ---
def save_sale_to_db(name, barber, price, cliente_nombre=""):
    c_barbero = price * 0.60
    c_empresa = price * 0.40
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO sales (service_name, barber_name, price, comision_barbero, comision_empresa, date, cliente_nombre) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (name, barber, price, c_barbero, c_empresa, fecha_actual, cliente_nombre))
        conn.commit()
        conn.close()
        return True
    except: return False

def save_venta_completa(items, barber, cliente_nombre="", cliente_documento="", ticket_text=""):
    nombres = " + ".join(i["nombre"] for i in items)
    total_venta = sum(i["precio"] for i in items)
    
    # Inicializamos los contadores en cero
    total_barbero = 0
    total_lavado = 0
    total_local = 0
    
    # RECORREMOS CADA ITEM PARA SUMAR SUS VALORES ESPECÍFICOS
    for item in items:
        nombre_servicio = item["nombre"]
        # Buscamos el servicio en nuestra nueva configuración
        if nombre_servicio in SERVICIOS_CONFIG:
            datos = SERVICIOS_CONFIG[nombre_servicio]
            total_barbero += datos["barbero"]
            total_lavado += datos["lavado"]
            total_local += datos["local"]
    
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        # Insertamos los valores exactos que sumamos arriba
        cursor.execute('''INSERT INTO sales (
                            service_name, barber_name, price, 
                            comision_barbero, comision_empresa, lavado_cabezal, 
                            date, cliente_nombre, cliente_documento, ticket_text
                          ) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (nombres, barber, total_venta, 
                        total_barbero, total_local, total_lavado, 
                        fecha_actual, cliente_nombre, cliente_documento, ticket_text))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

def delete_sale(sale_id):
    try:
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        conn.commit()
        conn.close()
        return True
    except: return False

def login_history_window():
    login_win = ctk.CTkToplevel()
    login_win.title("Acceso al Historial")
    login_win.geometry("300x320") # Aumentamos un poco el alto
    
    login_win.lift()
    login_win.attributes('-topmost', True)
    login_win.focus_force()
    login_win.grab_set() 

    ctk.CTkLabel(login_win, text="Seleccione Usuario", font=("Arial", 14, "bold")).pack(pady=(20, 5))
    
    user_var = ctk.StringVar(value="Trabajador")
    
    # Campo de contraseña (lo creamos primero para usarlo en la lógica)
    lbl_pass = ctk.CTkLabel(login_win, text="Contraseña Admin:")
    entry_pass = ctk.CTkEntry(login_win, show="*", width=200)

    def toggle_pass_field(choice):
        if choice == "Administrador":
            lbl_pass.pack(pady=(10, 0))
            entry_pass.pack(pady=(5, 10))
        else:
            lbl_pass.pack_forget()
            entry_pass.pack_forget()

    combo_user = ctk.CTkOptionMenu(login_win, variable=user_var, 
                                   values=["Trabajador", "Administrador"], 
                                   command=toggle_pass_field, width=200)
    combo_user.pack(pady=10)

    def acceder():
        rol = user_var.get()
        if rol == "Administrador":
            # AQUÍ CAMBIAS LA CONTRASEÑA
            if entry_pass.get() == "admin123": 
                login_win.destroy()
                open_history_window(rol)
            else:
                messagebox.showerror("Error", "Contraseña de Administrador incorrecta", parent=login_win)
        else:
            login_win.destroy()
            open_history_window(rol) 

    btn_entrar = ctk.CTkButton(login_win, text="Entrar al Sistema", command=acceder, 
                               fg_color=COLOR_CAJA, width=200)
    btn_entrar.pack(pady=20)


# --- VENTANA DE HISTORIAL Y CIERRE ---
# --- VENTANA DE HISTORIAL Y CIERRE ---
def open_history_window(rol):
    history_win = ctk.CTkToplevel()
    history_win.title("Sistema de Cierre de Caja")
    history_win.geometry("1100x750")
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    # --- VARIABLES DE CONTROL (Faltaban en tu código) ---
    filtro_var = ctk.StringVar(value="Todos")
    
    # --- FILTROS ---
    filter_frame = ctk.CTkFrame(history_win, fg_color="#1e1e1e")
    filter_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(filter_frame, text="Desde (YYYY-MM-DD):").pack(side="left", padx=5)
    entry_desde = ctk.CTkEntry(filter_frame, width=120)
    entry_desde.insert(0, fecha_hoy)
    entry_desde.pack(side="left", padx=5)

    ctk.CTkLabel(filter_frame, text="Hasta (YYYY-MM-DD):").pack(side="left", padx=5)
    entry_hasta = ctk.CTkEntry(filter_frame, width=120)
    entry_hasta.insert(0, fecha_hoy)
    entry_hasta.pack(side="left", padx=5)

    ctk.CTkOptionMenu(filter_frame, variable=filtro_var, values=["Todos"] + BARBEROS).pack(side="left", padx=10)

    # --- TABLA ---
    table_frame = ctk.CTkFrame(history_win)
    table_frame.pack(expand=True, fill="both", padx=20, pady=10)

    columns = ("id", "servicio", "barbero", "total", "com_barbero", "empresa","lavados", "hora")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    
    for col in columns:
        tree.heading(col, text=col.upper())
        tree.column(col, width=90, anchor="center")
    
    tree.pack(side="left", expand=True, fill="both")

    # --- LABELS DE RESUMEN ---
    summary_frame = ctk.CTkFrame(history_win, fg_color="transparent")
    summary_frame.pack(fill="x", padx=20)

    lbl_total = ctk.CTkLabel(summary_frame, text="Total: $0", font=("Arial", 14, "bold"))
    lbl_total.pack(side="left", padx=20)
    
    lbl_barbero = ctk.CTkLabel(summary_frame, text="Comisión: $0", font=("Arial", 14), text_color=COLOR_BARBERO)
    lbl_barbero.pack(side="left", padx=20)

    lbl_local = ctk.CTkLabel(summary_frame, text="Local: $0", font=("Arial", 14), text_color=COLOR_CAJA)
    lbl_local.pack(side="left", padx=20)

    lbl_lavados = ctk.CTkLabel(summary_frame, text="Lavados Admin: $0", font=("Arial", 14), text_color="#2ecc71")
    lbl_lavados.pack(side="left", padx=20)

    # --- LÓGICA INTERNA ---
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
        t_b = t_bar = t_loc = t_lav = 0
        for row in cursor.fetchall():
            t_b += row[3]; t_bar += row[4]; t_loc += row[5]; t_lav += row[6]
            hora = row[7].split(" ")[1] if " " in row[7] else "00:00"
            tree.insert("", "end", values=(row[0], row[1], row[2], f"${row[3]:,.0f}", 
                                       f"${row[4]:,.0f}", f"${row[5]:,.0f}", 
                                       f"${row[6]:,.0f}", hora))
        # Actualiza el texto del label que creamos arriba
        lbl_lavados.configure(text=f"Lavados Admin\n${t_lav:,.0f}")
        conn.close()
        
        lbl_total.configure(text=f"Total Rango\n${t_b:,.0f}")
        lbl_barbero.configure(text=f"Comisión {barber}\n${t_bar:,.0f}")
        lbl_local.configure(text=f"Ganancia Local\n${t_loc:,.0f}")

    def ver_ticket_seleccionado():
        selected = tree.selection()
        if not selected:
            return messagebox.showwarning("Atención", "Selecciona una venta de la lista", parent=history_win)
        
        sale_id = tree.item(selected)['values'][0]
        conn = sqlite3.connect("barberia.db")
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_text FROM sales WHERE id = ?", (sale_id,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado and resultado[0]:
            t = ctk.CTkToplevel()
            t.title(f"Ticket Venta #{sale_id}")
            t.geometry("400x520")
            t.lift()
            txt = ctk.CTkTextbox(t, font=("Courier", 12), width=375, height=430)
            txt.pack(padx=10, pady=10)
            txt.insert("end", resultado[0])
            txt.configure(state="disabled")
            ctk.CTkButton(t, text="Cerrar", command=t.destroy).pack(pady=5)
        else:
            messagebox.showinfo("Info", "No hay ticket guardado para esta venta.", parent=history_win)

    def handle_delete():
        selected = tree.selection()
        if not selected: return
        item_id = tree.item(selected)['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Borrar venta #{item_id}?", parent=history_win):
            if delete_sale(item_id):
                actualizar_tabla()

# --- PANEL DE ACCIONES (Limpio y sin duplicados) ---
    actions_frame = ctk.CTkFrame(history_win, fg_color="transparent")
    actions_frame.pack(fill="x", padx=20, pady=20)

    # El botón de filtrar va en el frame de arriba (filter_frame)
    ctk.CTkButton(filter_frame, text="🔍 Filtrar", command=actualizar_tabla, fg_color=COLOR_CAJA).pack(side="left", padx=10)

    # Botón Eliminar: Se configura según el rol
    btn_eliminar = ctk.CTkButton(actions_frame, text="🗑 Eliminar Venta", 
                                 fg_color="#922b21", command=handle_delete)
    btn_eliminar.pack(side="left", padx=10)

    if rol == "Trabajador":
        btn_eliminar.configure(state="disabled", text="🗑 Bloqueado (Solo Admin)")

    # Botón Ver Ticket
    ctk.CTkButton(actions_frame, text="👁 Ver Ticket", 
                  fg_color="#5d6d7e", command=ver_ticket_seleccionado).pack(side="left", padx=10)

    actualizar_tabla()

# --- VENTANA PRINCIPAL ---
# --- VENTANA PRINCIPAL CORREGIDA ---
def main_window():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("BarberShop Professional POS")
    
    # Ajustamos a una altura más estándar para laptops (800)
    root.geometry("520x800") 
    root.resizable(True, True)

    # --- CONTENEDOR CON SCROLL (Para que nada se pierda) ---
    main_scroll = ctk.CTkScrollableFrame(root, fg_color="transparent")
    main_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    ctk.CTkLabel(main_scroll, text="💈 TAJAMARES BARBER SHOP 💈", font=("Arial", 24, "bold")).pack(pady=15)

    # Selector Barbero
    select_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
    select_frame.pack(pady=3)
    ctk.CTkLabel(select_frame, text="BARBERO DE TURNO:", font=("Arial", 12, "bold")).pack()
    barber_selector = ctk.CTkOptionMenu(select_frame, values=BARBEROS, width=300, height=38, font=("Arial", 13))
    barber_selector.pack(pady=4)


    carrito = []

    def actualizar_resumen_carrito():
        for widget in frame_carrito_items.winfo_children():
            widget.destroy()
        if not carrito:
            ctk.CTkLabel(frame_carrito_items, text="(sin servicios agregados)", text_color="#888").pack(pady=4)
            btn_finalizar.configure(state="disabled")
            lbl_total_carrito.configure(text="")
            return
        for i, item in enumerate(carrito):
            fila = ctk.CTkFrame(frame_carrito_items, fg_color="transparent")
            fila.pack(fill="x", padx=10, pady=1)
            ctk.CTkLabel(fila, text=f"• {item['nombre']}  ${item['precio']:,.0f}",
                         font=("Arial", 11), anchor="w").pack(side="left", expand=True, fill="x")
            ctk.CTkButton(fila, text="✕", width=26, height=22, fg_color="#7b241c",
                          command=lambda idx=i: quitar_del_carrito(idx)).pack(side="right")
        total = sum(x["precio"] for x in carrito)
        lbl_total_carrito.configure(text=f"TOTAL: ${total:,.0f}")
        btn_finalizar.configure(state="normal")

    def quitar_del_carrito(idx):
        carrito.pop(idx)
        actualizar_resumen_carrito()

    def agregar_al_carrito(nombre, precio):
        carrito.append({"nombre": nombre, "precio": precio})
        actualizar_resumen_carrito()

    def finalizar_venta():
            if not carrito:
                return
            win = ctk.CTkToplevel()
            win.title("Datos del cliente")
            win.geometry("360x300") # Aumentamos altura para el nuevo campo
            win.resizable(False, False)
            win.lift()
            win.focus_force()

            ctk.CTkLabel(win, text="Nombre del cliente:", font=("Arial", 12, "bold")).pack(pady=(15, 0))
            entry_cliente = ctk.CTkEntry(win, width=280, placeholder_text="Ej: Juan Pérez")
            entry_cliente.pack(pady=5)

            # NUEVO CAMPO PARA DOCUMENTO
            ctk.CTkLabel(win, text="Documento / CC:", font=("Arial", 12, "bold")).pack(pady=(10, 0))
            entry_doc = ctk.CTkEntry(win, width=280, placeholder_text="Ej: 1002345678")
            entry_doc.pack(pady=5)

            def confirmar():
                cliente = entry_cliente.get().strip() or "Cliente"
                documento = entry_doc.get().strip() or "N/A" # Capturamos el documento
                barbero = barber_selector.get()
                items_snapshot = carrito[:]
                total = sum(x["precio"] for x in items_snapshot)
                
                linea = "─" * 40
                fecha_ticket = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # --- TICKET ACTUALIZADO CON DOCUMENTO ---
                ticket_text = (
                    f"\n{'💈 TAJAMARES BARBER SHOP 💈':^40}\n"
                    f"{linea}\n"
                    f"  Cliente : {cliente}\n"
                    f"  C.C.    : {documento}\n" # Se añade al ticket
                    f"  Barbero : {barbero}\n"
                    f"  Fecha   : {fecha_ticket}\n"
                    f"{linea}\n"
                    f"  SERVICIOS:\n"
                )
                for item in items_snapshot:
                    nombre_corto = item['nombre'][:24]
                    ticket_text += f"  · {nombre_corto:<24} ${item['precio']:>8,.0f}\n"

                ticket_text += (
                    f"\n{linea}\n"
                    f"  {'TOTAL':<28} ${total:>8,.0f}\n"
                    f"{linea}\n"
                    f"     ¡Gracias por su visita! 🙌\n"
                )
                
                # Guardamos incluyendo el documento
                save_venta_completa(items_snapshot, barbero, cliente_nombre=cliente, 
                                    cliente_documento=documento, ticket_text=ticket_text)
                
                carrito.clear()
                actualizar_resumen_carrito()
                win.destroy()
                root.after(200, lambda: mostrar_ticket(ticket_text))

            ctk.CTkButton(win, text="✅ Confirmar y generar ticket", command=confirmar,
                        fg_color=COLOR_CAJA).pack(pady=20)
            win.after(100, entry_cliente.focus_set)

    def mostrar_ticket(texto_listo):
            t = ctk.CTkToplevel()
            t.title("Ticket de Venta")
            t.geometry("400x540")
            t.resizable(False, False)
            t.lift()
            t.focus_force()

            txt = ctk.CTkTextbox(t, font=("Courier", 12), width=375, height=430)
            txt.pack(padx=10, pady=10)
            txt.insert("end", texto_listo)
            txt.configure(state="disabled")
            ctk.CTkButton(t, text="Cerrar", command=t.destroy, width=120).pack(pady=5)

# --- BOTONES DE SERVICIOS (Generados Automáticamente) ---
    frame_btns = ctk.CTkFrame(main_scroll, fg_color="#2b2b2b", corner_radius=15)
    frame_btns.pack(pady=8, padx=30, fill="x")
    
    ctk.CTkLabel(frame_btns, text="SERVICIOS DISPONIBLES", 
                 font=("Arial", 13, "bold"), text_color="#aaaaaa").pack(pady=4)

    # Ahora recorremos nuestra nueva SERVICIOS_CONFIG
    for nombre, datos in SERVICIOS_CONFIG.items():
        precio_total = datos["precio"]
        ctk.CTkButton(
            frame_btns, 
            text=f"{nombre} (${precio_total:,.0f})",
            # Al hacer clic, pasamos el nombre y el precio al carrito
            command=lambda n=nombre, p=precio_total: agregar_al_carrito(n, p),
            height=40, 
            font=("Arial", 12, "bold"),
            fg_color="#3b3b3b", 
            hover_color="#4b4b4b"
        ).pack(pady=3, padx=15, fill="x")

    # --- CARRITO ---
    frame_carrito = ctk.CTkFrame(main_scroll, fg_color="#000000", corner_radius=10)
    frame_carrito.pack(pady=6, padx=30, fill="x")
    ctk.CTkLabel(frame_carrito, text="🧾 Venta en curso",
                 font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(pady=(6, 2))

    frame_carrito_items = ctk.CTkFrame(frame_carrito, fg_color="transparent", height=90)
    frame_carrito_items.pack(fill="x")
    frame_carrito_items.pack_propagate(False) 
    
    lbl_total_carrito = ctk.CTkLabel(frame_carrito, text="",
                                      font=("Arial", 13, "bold"), text_color=COLOR_CAJA)
    lbl_total_carrito.pack(pady=4)

    # --- BOTONES DE ACCIÓN FINAL (Dentro del scroll para asegurar visibilidad) ---
    btn_finalizar = ctk.CTkButton(main_scroll, text="✅ FINALIZAR VENTA Y GENERAR TICKET",
                                  command=finalizar_venta,
                                  fg_color=COLOR_CAJA, hover_color="#000000",
                                  height=52, font=("Arial", 13, "bold"), state="disabled")
    btn_finalizar.pack(pady=6, padx=30, fill="x")

    btn_reporte = ctk.CTkButton(main_scroll, text="📊 VER REPORTES Y CIERRE DE CAJA",
                                command=login_history_window, # ← NUEVA FUNCIÓN
                                fg_color=COLOR_BARBERO, hover_color="#2e6da4",
                                height=52, font=("Arial", 13, "bold"))
    btn_reporte.pack(pady=(0, 20), padx=30, fill="x")

    actualizar_resumen_carrito()
    root.mainloop()

if __name__ == "__main__":
    create_db()
    main_window()