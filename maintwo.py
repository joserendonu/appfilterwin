import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

from config import DATA_FILE, IMG_FOLDER

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)


class InventarioApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Productos")
        self.root.geometry("750x650")

        self.data = self.cargar_datos()
        self.editando = None
        self.imagenes_guardadas = []

        # BUSCADOR
        self.busqueda_var = tk.StringVar()
        self.busqueda_var.trace("w", self.actualizar_lista)
        tk.Entry(root, textvariable=self.busqueda_var).pack(fill="x", padx=10, pady=5)

        # CONTENEDOR CON SCROLL
        self.frame_lista = tk.Frame(root)
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.frame_lista)
        self.scrollbar = ttk.Scrollbar(self.frame_lista, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        tk.Button(root, text="Agregar Producto", command=self.popup_agregar).pack(pady=10)

        self.actualizar_lista()

    # ---------- DATOS ----------

    def cargar_datos(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def guardar_datos(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    # ---------- LISTA ----------

    def actualizar_lista(self, *args):
        texto = self.busqueda_var.get().lower()
        self.imagenes_guardadas.clear()

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for item in self.data:
            combinado = f"{item.get('nombre','')} {item.get('ref','')} {item.get('desc','')}".lower()
            if texto in combinado:
                self.crear_tarjeta(item)

    def crear_tarjeta(self, item):
        frame = tk.Frame(self.scrollable_frame, bd=1, relief="solid", padx=10, pady=10)
        frame.pack(fill="x", pady=5)

        # IMAGEN
        if item.get("img") and os.path.exists(item["img"]):
            try:
                img = Image.open(item["img"])
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.imagenes_guardadas.append(photo)

                tk.Label(frame, image=photo).pack()
            except:
                tk.Label(frame, text="Error cargando imagen").pack()
        else:
            tk.Label(frame, text="Sin imagen", fg="gray").pack()

        tk.Label(frame, text=f"Nombre: {item.get('nombre','')}", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Referencia: {item.get('ref','')}").pack(anchor="w")
        tk.Label(frame, text=f"Descripción: {item.get('desc','')}").pack(anchor="w")

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Editar", command=lambda: self.popup_editar(item)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Eliminar", command=lambda: self.eliminar(item)).pack(side="left", padx=5)

    # ---------- POPUPS ----------

    def popup_agregar(self):
        self.editando = None
        self.popup_formulario("Agregar Producto")

    def popup_editar(self, item):
        self.editando = item
        self.popup_formulario("Editar Producto", item)

    def popup_formulario(self, titulo, item=None):
        ventana = tk.Toplevel(self.root)
        ventana.title(titulo)
        ventana.geometry("400x500")

        tk.Label(ventana, text="Nombre").pack()
        nombre = tk.Entry(ventana)
        nombre.pack(fill="x", padx=10)

        tk.Label(ventana, text="Referencia").pack()
        ref = tk.Entry(ventana)
        ref.pack(fill="x", padx=10)

        tk.Label(ventana, text="Descripción").pack()
        desc = tk.Entry(ventana)
        desc.pack(fill="x", padx=10)

        ruta_img = {"valor": ""}

        # VISTA PREVIA
        preview_label = tk.Label(ventana)
        preview_label.pack(pady=10)

        def mostrar_preview(ruta):
            if ruta and os.path.exists(ruta):
                img = Image.open(ruta)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                preview_label.config(image=photo)
                preview_label.image = photo

        if item:
            nombre.insert(0, item.get("nombre", ""))
            ref.insert(0, item.get("ref", ""))
            desc.insert(0, item.get("desc", ""))
            ruta_img["valor"] = item.get("img", "")
            mostrar_preview(ruta_img["valor"])

        def seleccionar_imagen():
            archivo = filedialog.askopenfilename(
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg")]
            )
            if archivo:
                destino = os.path.join(IMG_FOLDER, os.path.basename(archivo))
                shutil.copy(archivo, destino)
                ruta_img["valor"] = destino
                mostrar_preview(destino)

        tk.Button(ventana, text="Seleccionar Imagen", command=seleccionar_imagen).pack(pady=5)

        def guardar():
            if not nombre.get() or not ref.get():
                messagebox.showwarning("Error", "Nombre y Referencia son obligatorios")
                return

            if self.editando:
                self.editando["nombre"] = nombre.get()
                self.editando["ref"] = ref.get()
                self.editando["desc"] = desc.get()
                self.editando["img"] = ruta_img["valor"]
            else:
                self.data.append({
                    "nombre": nombre.get(),
                    "ref": ref.get(),
                    "desc": desc.get(),
                    "img": ruta_img["valor"]
                })

            self.guardar_datos()
            ventana.destroy()
            self.actualizar_lista()

        tk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)

    # ---------- ELIMINAR ----------

    def eliminar(self, item):
        if messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
            self.data.remove(item)
            self.guardar_datos()
            self.actualizar_lista()


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()