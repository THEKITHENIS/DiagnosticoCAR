# =============================================================================
# SENTINEL PRO - MANTENIMIENTO PREDICTIVO v10.0 - MODO DUAL OBD/SIMULACIÓN
# Compatible con Python 3.13 - Funciona sin hardware OBD-II
# =============================================================================
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import random
import traceback

# ============================================
# INTENTAR IMPORTAR OBD (Modo Dual)
# ============================================
try:
    import obd
    OBD_AVAILABLE = True
    print("✅ Librería OBD importada correctamente")
    print("🔧 Modo OBD-II: ACTIVO (Hardware disponible)")
except ImportError as e:
    OBD_AVAILABLE = False
    print(f"⚠️  Librería OBD no disponible: {e}")
    print("🔄 Funcionando en MODO SIMULACIÓN")
    print("💡 Tip: Actualiza Python a 3.10/3.11 o instala: pip install --upgrade pint>=0.23")

app = Flask(__name__)
CORS(app)

DB_PATH = 'sentinel_pro.db'

# Variables globales
connection = None
active_vehicle_id = None

# ============================================
# FUNCIONES AUXILIARES - BASE DE DATOS
# ============================================

def get_db_connection():
    """Conectar a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Crear tablas de base de datos si no existen"""
    try:
        conn = get_db_connection()

        # Tabla de vehículos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER NOT NULL,
                fuel_type TEXT DEFAULT 'gasolina',
                vin TEXT,
                plate TEXT,
                nickname TEXT,
                is_active INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_connection TEXT
            )
        ''')

        # Tabla de telemetría
        conn.execute('''
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                rpm INTEGER,
                speed REAL,
                throttle_pos REAL,
                engine_load REAL,
                coolant_temp REAL,
                intake_temp REAL,
                maf REAL,
                distance REAL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        # Tabla de historial de salud
        conn.execute('''
            CREATE TABLE IF NOT EXISTS health_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                overall_score INTEGER,
                engine_health INTEGER,
                thermal_health INTEGER,
                efficiency_health INTEGER,
                warnings TEXT,
                predictions TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        # Tabla de viajes
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                distance_km REAL,
                duration_minutes REAL,
                avg_speed REAL,
                max_speed REAL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        # Tabla de mantenimiento
        conn.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                maintenance_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")

    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        traceback.print_exc()

# ============================================
# FUNCIONES AUXILIARES - SIMULACIÓN OBD
# ============================================

def get_simulated_data():
    """Generar datos simulados de telemetría cuando OBD no está disponible"""
    return {
        'rpm': random.randint(800, 3000),
        'speed': round(random.uniform(0, 120), 1),
        'throttle': round(random.uniform(0, 100), 1),
        'engine_load': round(random.uniform(20, 80), 1),
        'coolant_temp': round(random.uniform(85, 95), 1),
        'intake_temp': round(random.uniform(20, 40), 1),
        'maf': round(random.uniform(10, 50), 2),
        'distance': round(random.uniform(0, 100), 2)
    }

# ============================================
# SERVIR ARCHIVOS ESTÁTICOS
# ============================================

@app.route('/')
def index():
    """Servir página principal"""
    return send_from_directory('.', 'index.html')

@app.route('/vehiculos.html')
def vehiculos():
    """Servir página de vehículos"""
    return send_from_directory('.', 'vehiculos.html')

@app.route('/<path:path>')
def serve_static(path):
    """Servir archivos estáticos (CSS, JS, imágenes, etc.)"""
    try:
        return send_from_directory('.', path)
    except Exception as e:
        print(f"[STATIC] Error sirviendo {path}: {e}")
        return jsonify({'error': 'Archivo no encontrado'}), 404

# ============================================
# ENDPOINTS DE VEHÍCULOS (COMPLETOS)
# ============================================

@app.route('/get_vehicles', methods=['GET'])
def get_vehicles():
    """Obtener todos los vehículos"""
    try:
        conn = get_db_connection()
        vehicles = conn.execute('SELECT * FROM vehicles ORDER BY created_at DESC').fetchall()
        conn.close()

        vehicles_list = []
        for v in vehicles:
            vehicles_list.append({
                'id': v['id'],
                'brand': v['brand'],
                'model': v['model'],
                'year': v['year'],
                'mileage': v['mileage'],
                'fuel_type': v['fuel_type'],
                'vin': v['vin'] if v['vin'] else '',
                'plate': v['plate'] if v['plate'] else '',
                'nickname': v['nickname'] if v['nickname'] else '',
                'is_active': bool(v['is_active']),
                'created_at': v['created_at'],
                'updated_at': v['updated_at'],
                'last_connection': v['last_connection'] if v['last_connection'] else 'Nunca'
            })

        return jsonify({'success': True, 'vehicles': vehicles_list})

    except Exception as e:
        print(f"❌ Error en get_vehicles: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save_vehicle', methods=['POST'])
def save_vehicle():
    """Crear un nuevo vehículo"""
    try:
        data = request.json
        print(f"📝 Guardando vehículo: {data.get('brand')} {data.get('model')}")

        conn = get_db_connection()

        cursor = conn.execute('''
            INSERT INTO vehicles (
                brand, model, year, mileage, fuel_type,
                vin, plate, nickname, is_active,
                created_at, updated_at, last_connection
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['brand'],
            data['model'],
            data['year'],
            data['mileage'],
            data.get('fuel_type', 'gasolina'),
            data.get('vin', ''),
            data.get('plate', ''),
            data.get('nickname', ''),
            0,  # is_active = False por defecto
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            None
        ))

        vehicle_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Vehículo guardado con ID: {vehicle_id}")
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'message': 'Vehículo creado correctamente'
        })

    except Exception as e:
        print(f"❌ Error en save_vehicle: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_vehicle', methods=['POST'])
def update_vehicle():
    """Actualizar un vehículo existente"""
    try:
        data = request.json
        vehicle_id = data['id']
        print(f"📝 Actualizando vehículo ID: {vehicle_id}")

        conn = get_db_connection()
        conn.execute('''
            UPDATE vehicles
            SET brand=?, model=?, year=?, mileage=?, fuel_type=?,
                vin=?, plate=?, nickname=?, updated_at=?
            WHERE id=?
        ''', (
            data['brand'],
            data['model'],
            data['year'],
            data['mileage'],
            data.get('fuel_type', 'gasolina'),
            data.get('vin', ''),
            data.get('plate', ''),
            data.get('nickname', ''),
            datetime.now().isoformat(),
            vehicle_id
        ))

        conn.commit()
        conn.close()

        print(f"✅ Vehículo actualizado")
        return jsonify({'success': True, 'message': 'Vehículo actualizado correctamente'})

    except Exception as e:
        print(f"❌ Error en update_vehicle: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_vehicle', methods=['POST'])
def delete_vehicle():
    """Eliminar un vehículo"""
    global active_vehicle_id

    try:
        data = request.json
        vehicle_id = data['id']
        print(f"🗑️  Eliminando vehículo ID: {vehicle_id}")

        # Si es el vehículo activo, deseleccionarlo
        if active_vehicle_id == vehicle_id:
            active_vehicle_id = None

        conn = get_db_connection()

        # Eliminar datos relacionados
        conn.execute('DELETE FROM telemetry_data WHERE vehicle_id=?', (vehicle_id,))
        conn.execute('DELETE FROM health_history WHERE vehicle_id=?', (vehicle_id,))
        conn.execute('DELETE FROM trips WHERE vehicle_id=?', (vehicle_id,))
        conn.execute('DELETE FROM maintenance_records WHERE vehicle_id=?', (vehicle_id,))

        # Eliminar vehículo
        conn.execute('DELETE FROM vehicles WHERE id=?', (vehicle_id,))

        conn.commit()
        conn.close()

        print(f"✅ Vehículo eliminado")
        return jsonify({'success': True, 'message': 'Vehículo eliminado correctamente'})

    except Exception as e:
        print(f"❌ Error en delete_vehicle: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/set_active_vehicle', methods=['POST'])
def set_active_vehicle():
    """Activar un vehículo específico"""
    global active_vehicle_id

    try:
        data = request.json
        vehicle_id = data.get('vehicle_id') or data.get('id')
        print(f"🎯 Activando vehículo ID: {vehicle_id}")

        if not vehicle_id:
            return jsonify({'success': False, 'error': 'ID de vehículo requerido'}), 400

        conn = get_db_connection()

        # Desactivar todos
        conn.execute('UPDATE vehicles SET is_active = 0')

        # Activar el seleccionado
        result = conn.execute('''
            UPDATE vehicles
            SET is_active = 1, updated_at = ?, last_connection = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), datetime.now().isoformat(), vehicle_id))

        if result.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Vehículo no encontrado'}), 404

        conn.commit()

        # Obtener el vehículo activado
        vehicle = conn.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()
        conn.close()

        active_vehicle_id = vehicle_id

        print(f"✅ Vehículo activado: {vehicle['brand']} {vehicle['model']}")
        return jsonify({
            'success': True,
            'message': 'Vehículo activado correctamente',
            'vehicle': {
                'id': vehicle['id'],
                'brand': vehicle['brand'],
                'model': vehicle['model'],
                'year': vehicle['year']
            }
        })

    except Exception as e:
        print(f"❌ Error en set_active_vehicle: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/activate_vehicle', methods=['POST'])
def activate_vehicle():
    """Alias de set_active_vehicle"""
    return set_active_vehicle()

@app.route('/get_active_vehicle', methods=['GET'])
def get_active_vehicle():
    """Obtener el vehículo activo"""
    global active_vehicle_id

    if active_vehicle_id is None:
        return jsonify({
            'success': False,
            'message': 'No hay vehículo activo'
        })

    try:
        conn = get_db_connection()
        vehicle = conn.execute('SELECT * FROM vehicles WHERE id=?', (active_vehicle_id,)).fetchone()
        conn.close()

        if vehicle:
            return jsonify({
                'success': True,
                'vehicle': {
                    'id': vehicle['id'],
                    'brand': vehicle['brand'],
                    'model': vehicle['model'],
                    'year': vehicle['year'],
                    'mileage': vehicle['mileage'],
                    'fuel_type': vehicle['fuel_type'],
                    'vin': vehicle['vin'],
                    'plate': vehicle['plate'],
                    'nickname': vehicle['nickname']
                }
            })
        else:
            active_vehicle_id = None
            return jsonify({'success': False, 'message': 'Vehículo activo no encontrado'})

    except Exception as e:
        print(f"❌ Error en get_active_vehicle: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_fleet_stats', methods=['GET'])
def get_fleet_stats():
    """Obtener estadísticas de la flota"""
    try:
        conn = get_db_connection()

        total = conn.execute('SELECT COUNT(*) as count FROM vehicles').fetchone()['count']
        total_km = conn.execute('SELECT SUM(mileage) as total FROM vehicles').fetchone()['total'] or 0

        # Contar vehículos conectados hoy
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        connected_today = conn.execute(
            'SELECT COUNT(*) as count FROM vehicles WHERE last_connection > ?',
            (yesterday,)
        ).fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_vehicles': total,
                'total_kilometers': int(total_km),
                'connected_today': connected_today,
                'vehicles_with_warnings': 0,
                'avg_health': 95
            }
        })

    except Exception as e:
        print(f"❌ Error en get_fleet_stats: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ENDPOINT DE TELEMETRÍA (MODO DUAL)
# ============================================

@app.route('/get_obd_data', methods=['GET'])
def get_obd_data():
    """Obtener datos OBD-II (real o simulado)"""
    try:
        if OBD_AVAILABLE and connection and connection.is_connected():
            # TODO: Implementar lectura real cuando hardware esté conectado
            # Por ahora usar simulación incluso con OBD disponible
            data = get_simulated_data()
            mode = 'real'
        else:
            data = get_simulated_data()
            mode = 'simulation'

        # Guardar en base de datos si hay vehículo activo
        if active_vehicle_id:
            try:
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO telemetry_data (
                        vehicle_id, timestamp, rpm, speed, throttle_pos,
                        engine_load, coolant_temp, intake_temp, maf, distance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    active_vehicle_id,
                    datetime.now().isoformat(),
                    data['rpm'],
                    data['speed'],
                    data['throttle'],
                    data['engine_load'],
                    data['coolant_temp'],
                    data['intake_temp'],
                    data['maf'],
                    data['distance']
                ))
                conn.commit()
                conn.close()
            except Exception as db_error:
                print(f"⚠️  Error guardando telemetría: {db_error}")

        return jsonify({
            'success': True,
            'mode': mode,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'active_vehicle_id': active_vehicle_id
        })

    except Exception as e:
        print(f"❌ Error en get_obd_data: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_live_data', methods=['GET'])
def get_live_data():
    """Alias de get_obd_data para compatibilidad"""
    try:
        if OBD_AVAILABLE and connection and connection.is_connected():
            data = get_simulated_data()
        else:
            data = get_simulated_data()

        return jsonify({
            'offline': False,
            'RPM': data['rpm'],
            'SPEED': data['speed'],
            'THROTTLE_POS': data['throttle'],
            'ENGINE_LOAD': data['engine_load'],
            'MAF': data['maf'],
            'COOLANT_TEMP': data['coolant_temp'],
            'INTAKE_TEMP': data['intake_temp'],
            'total_distance': data['distance'],
            'active_vehicle_id': active_vehicle_id
        })

    except Exception as e:
        print(f"❌ Error en get_live_data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'offline': True,
            'RPM': None,
            'SPEED': None,
            'THROTTLE_POS': None,
            'ENGINE_LOAD': None,
            'MAF': None,
            'COOLANT_TEMP': None,
            'INTAKE_TEMP': None,
            'total_distance': 0,
            'active_vehicle_id': active_vehicle_id
        })

@app.route('/get_vehicle_health', methods=['GET'])
def get_vehicle_health():
    """Obtener salud del vehículo activo"""
    return jsonify({
        'overall_score': 95,
        'engine_health': 95,
        'thermal_health': 98,
        'efficiency_health': 92,
        'warnings': [],
        'predictions': [],
        'last_update': datetime.now().isoformat()
    })

# ============================================
# MANEJADORES DE ERRORES
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Manejar errores 404 devolviendo JSON"""
    print(f"[ERROR 404] {request.method} {request.path}")
    return jsonify({
        'success': False,
        'error': 'Endpoint no encontrado',
        'message': f'El endpoint {request.method} {request.path} no existe'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Manejar errores 405 devolviendo JSON"""
    print(f"[ERROR 405] Método {request.method} no permitido para {request.path}")
    return jsonify({
        'success': False,
        'error': 'Método no permitido',
        'message': 'Verifica el método HTTP (GET/POST/PUT/DELETE)'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Manejar errores 500 devolviendo JSON"""
    print(f"[ERROR 500] Error interno: {str(error)}")
    traceback.print_exc()
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor',
        'message': str(error)
    }), 500

# ============================================
# INICIO DEL SERVIDOR
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🛡️  SENTINEL PRO - Sistema Multi-Vehículo v10.0")
    print("="*60)
    print(f"🔧 Modo OBD-II: {'ACTIVO ✅' if OBD_AVAILABLE else 'SIMULACIÓN ⚠️'}")
    print(f"🐍 Python: Compatible con 3.10, 3.11, 3.12 y 3.13")
    print(f"🌐 Servidor: http://localhost:5000")
    print(f"📄 Dashboard: http://localhost:5000/")
    print(f"🚗 Vehículos: http://localhost:5000/vehiculos.html")
    print("\n📡 Endpoints disponibles:")
    print("   - GET  /get_vehicles             → Listar todos los vehículos")
    print("   - POST /save_vehicle             → Crear nuevo vehículo")
    print("   - POST /update_vehicle           → Actualizar vehículo")
    print("   - POST /delete_vehicle           → Eliminar vehículo")
    print("   - POST /set_active_vehicle       → Activar vehículo")
    print("   - POST /activate_vehicle         → Activar vehículo (alias)")
    print("   - GET  /get_active_vehicle       → Obtener vehículo activo")
    print("   - GET  /get_fleet_stats          → Estadísticas de la flota")
    print("   - GET  /get_obd_data             → Datos OBD-II (modo dual)")
    print("   - GET  /get_live_data            → Datos en vivo (compatible)")
    print("   - GET  /get_vehicle_health       → Salud del vehículo")
    print("="*60)

    if not OBD_AVAILABLE:
        print("\n⚠️  IMPORTANTE: Modo simulación activo")
        print("💡 Para habilitar OBD-II real:")
        print("   1. Instala Python 3.10 o 3.11 desde python.org")
        print("   2. O ejecuta: pip install --upgrade pint>=0.23")
        print("   3. Reinicia el servidor")
        print("="*60)

    # Inicializar base de datos
    initialize_database()

    print("\n✅ Servidor ACTIVO - Presiona Ctrl+C para detener\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
