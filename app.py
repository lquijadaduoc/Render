import os
import pandas as pd
from flask import Flask, render_template, request, flash
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = "super_secreto_para_sesiones" # Necesario para mostrar mensajes (flashes)

# Configuramos la conexión a Supabase (Render inyectará esto como variable de entorno)
# Formato esperado: postgresql://postgres.tu_proyecto:tu_password@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db") # Usa SQLite local si no hay URL
engine = create_engine(DATABASE_URL)

@app.route("/", methods=["GET"])
def index():
    # Solo muestra la página con el formulario
    return render_template("index.html", tabla_html=None)

@app.route("/upload", methods=["POST"])
def upload():
    if 'archivo_excel' not in request.files:
        flash("No se envió ningún archivo", "danger")
        return render_template("index.html", tabla_html=None)
    
    archivo = request.files['archivo_excel']
    
    if archivo.filename == '':
        flash("Ningún archivo seleccionado", "danger")
        return render_template("index.html", tabla_html=None)

    try:
        # 1. Leer el Excel en memoria con Pandas
        df = pd.read_excel(archivo)
        total_filas = len(df)
        
        # 2. Carga masiva a Supabase
        # 'if_exists="replace"' borra la tabla vieja y la crea de nuevo. 
        # Cambia a "append" si quieres sumar datos sin borrar.
        df.to_sql("productos", engine, if_exists="replace", index=False)
        
        # 3. Generar un preview HTML (Solo 50 filas para no colapsar el navegador)
        preview_df = df.head(50)
        
        # Pandas tiene una función genial para convertir un DataFrame directo a HTML con clases CSS
        tabla_html = preview_df.to_html(classes="table table-striped table-hover", index=False)
        
        flash(f"¡Éxito! Se cargaron {total_filas} registros en la base de datos.", "success")
        return render_template("index.html", tabla_html=tabla_html)
        
    except Exception as e:
        flash(f"Error procesando el archivo: {str(e)}", "danger")
        return render_template("index.html", tabla_html=None)

if __name__ == "__main__":
    # Debug=True solo para cuando lo corres en tu PC
    app.run(debug=True, port=5000)