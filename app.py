import os
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)
app.secret_key = "super_secreto_para_sesiones"

# Conexión a Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
engine = create_engine(DATABASE_URL)

# ==========================================
# RUTA 1: EL VISUALIZADOR (Pantalla Principal)
# ==========================================
@app.route("/", methods=["GET"])
def index():
    # 1. Capturar los filtros escritos por el usuario
    filtro_id = request.args.get('id', '')
    filtro_nombre = request.args.get('nombre', '')
    filtro_categoria = request.args.get('categoria', '')

    try:
        # 2. Construir la consulta SQL dinámica de forma segura
        query = "SELECT * FROM productos WHERE 1=1"
        params = {}

        if filtro_id:
            query += " AND id = %(id)s"
            params['id'] = int(filtro_id)
        if filtro_nombre:
            query += " AND nombre ILIKE %(nombre)s" # ILIKE es clave en Postgres para ignorar mayúsculas
            params['nombre'] = f"%{filtro_nombre}%"
        if filtro_categoria:
            query += " AND categoria ILIKE %(categoria)s"
            params['categoria'] = f"%{filtro_categoria}%"

        # Límite de seguridad: Mostrar máximo 100 para no colapsar la RAM del navegador
        query += " LIMIT 100"

        # 3. Ejecutar la consulta y convertir a HTML
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)

        if not df.empty:
            tabla_html = df.to_html(classes="table table-striped table-hover align-middle", index=False)
        else:
            tabla_html = "<div class='alert alert-info text-center'>No se encontraron productos con esos filtros.</div>"

        return render_template("index.html", tabla_html=tabla_html)

    except Exception as e:
        # Si la tabla no existe aún (porque no se ha subido el Excel)
        mensaje_error = "<div class='alert alert-warning text-center'>La base de datos está vacía. Por favor, carga un archivo Excel primero.</div>"
        return render_template("index.html", tabla_html=mensaje_error)

# ==========================================
# RUTA 2: LA CARGA DE DATOS
# ==========================================
@app.route("/upload", methods=["GET", "POST"])
def upload():
    # Si el usuario solo entra a la página, mostramos el formulario
    if request.method == "GET":
        return render_template("upload.html")

    # Si el usuario envía el formulario con el archivo
    if 'archivo_excel' not in request.files:
        flash("No se envió ningún archivo", "danger")
        return redirect(url_for('upload'))
    
    archivo = request.files['archivo_excel']
    
    if archivo.filename == '':
        flash("Ningún archivo seleccionado", "danger")
        return redirect(url_for('upload'))

    try:
        df = pd.read_excel(archivo)
        total_filas = len(df)
        
        # if_exists="replace" garantiza que se borre la tabla vieja y quede solo lo nuevo
        df.to_sql("productos", engine, if_exists="replace", index=False)
        
        flash(f"¡Éxito! Se borraron los datos anteriores y se cargaron {total_filas} registros nuevos.", "success")
        
        # Redirigimos al visualizador principal para ver los resultados
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f"Error procesando el archivo: {str(e)}", "danger")
        return redirect(url_for('upload'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)