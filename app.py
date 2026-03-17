from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# Función para conectarnos a la base de datos real
def get_db_connection():
    # USAMOS URI=TRUE y MODE=RO PARA MODO SOLO LECTURA
    # Si el archivo no existe, ahora dará error en vez de crearlo vacío.
    # ¡Asegúrate de tener tu archivo 'curso_sql.db' en la carpeta!
    conn = sqlite3.connect('file:curso_sql.db?mode=ro', uri=True, check_same_thread=False)
    # Permite acceder a las columnas por su nombre
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/')
def curso_sql():
    return render_template('index.html')

# ¡Este es el motor universal que evaluará TODOS tus ejercicios!
@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_sql():
    data = request.get_json()
    query = data.get('query', '')

    if not query.strip():
        return jsonify({'status': 'error', 'message': 'La consulta está vacía.'})

    # --- NUEVO: FILTRO DE SEGURIDAD (SOLO LECTURA) ---
    query_upper = query.strip().upper()
    if not (query_upper.startswith('SELECT') or query_upper.startswith('PRAGMA') or query_upper.startswith('WITH')):
        return jsonify({
            'status': 'error', 
            'message': '⛔ Operación denegada. Por seguridad, en este entorno público solo están permitidas las consultas de lectura (SELECT).'
        })
    # -------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Ejecutamos la query REAL en la base de datos
        cursor.execute(query)

        # 2. Como hemos bloqueado todo lo demás, sabemos seguro que es un SELECT
        filas = cursor.fetchall()
        
        # Extraemos los nombres reales de las columnas de la tabla
        columnas = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Convertimos los datos para enviarlos a la web
        datos_filas = [list(fila) for fila in filas]
        
        return jsonify({
            'status': 'success',
            'type': 'select',
            'columns': columnas,
            'rows': datos_filas,
            'message': f"{len(filas)} filas devueltas"
        })

    except sqlite3.Error as e:
        # 4. Si el usuario escribe mal el SQL, devolvemos el error exacto de la base de datos
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)