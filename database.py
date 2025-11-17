# =============================================================================
# SENTINEL PRO - MÓDULO DE BASE DE DATOS SQLite
# Gestión de múltiples vehículos con SQLite
# =============================================================================

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
import os

DATABASE_NAME = 'sentinel_pro.db'

# =============================================================================
# GESTOR DE CONEXIÓN A LA BASE DE DATOS
# =============================================================================

@contextmanager
def get_db_connection():
    """Context manager para gestionar conexiones a la base de datos"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# =============================================================================
# INICIALIZACIÓN DE BASE DE DATOS
# =============================================================================

def initialize_database():
    """Crea todas las tablas necesarias si no existen"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # TABLA: vehicles (vehículos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER NOT NULL,
                fuel_type TEXT NOT NULL,
                vin TEXT,
                plate TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # TABLA: telemetry_data (datos de telemetría)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rpm REAL,
                speed REAL,
                throttle_position REAL,
                engine_load REAL,
                coolant_temp REAL,
                intake_temp REAL,
                maf REAL,
                distance REAL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
            )
        ''')

        # TABLA: maintenance_records (registros de mantenimiento)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                maintenance_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
            )
        ''')

        # TABLA: ai_analysis (análisis de IA)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                health_score INTEGER,
                engine_health INTEGER,
                thermal_health INTEGER,
                efficiency_health INTEGER,
                predictions TEXT,
                warnings TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
            )
        ''')

        # ÍNDICES para mejorar rendimiento
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle
            ON telemetry_data(vehicle_id, timestamp DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle
            ON maintenance_records(vehicle_id, maintenance_date DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_analysis_vehicle
            ON ai_analysis(vehicle_id, analysis_date DESC)
        ''')

        print("[DATABASE] ✓ Base de datos inicializada correctamente")
        return True

# =============================================================================
# OPERACIONES CRUD - VEHÍCULOS
# =============================================================================

def create_vehicle(brand, model, year, mileage, fuel_type, vin=None, plate=None):
    """Crea un nuevo vehículo en la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vehicles (brand, model, year, mileage, fuel_type, vin, plate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (brand, model, year, mileage, fuel_type, vin, plate))
        return cursor.lastrowid

def get_all_vehicles():
    """Obtiene todos los vehículos registrados"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, brand, model, year, mileage, fuel_type, vin, plate,
                   created_at, updated_at
            FROM vehicles
            ORDER BY updated_at DESC
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_vehicle_by_id(vehicle_id):
    """Obtiene un vehículo específico por su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, brand, model, year, mileage, fuel_type, vin, plate,
                   created_at, updated_at
            FROM vehicles
            WHERE id = ?
        ''', (vehicle_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_vehicle(vehicle_id, brand, model, year, mileage, fuel_type, vin=None, plate=None):
    """Actualiza los datos de un vehículo existente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE vehicles
            SET brand = ?, model = ?, year = ?, mileage = ?,
                fuel_type = ?, vin = ?, plate = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (brand, model, year, mileage, fuel_type, vin, plate, vehicle_id))
        return cursor.rowcount > 0

def delete_vehicle(vehicle_id):
    """Elimina un vehículo y todos sus datos asociados (CASCADE)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
        return cursor.rowcount > 0

# =============================================================================
# OPERACIONES - TELEMETRÍA
# =============================================================================

def save_telemetry(vehicle_id, rpm, speed, throttle_position, engine_load,
                   coolant_temp=None, intake_temp=None, maf=None, distance=None):
    """Guarda un registro de telemetría para un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO telemetry_data
            (vehicle_id, rpm, speed, throttle_position, engine_load,
             coolant_temp, intake_temp, maf, distance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, rpm, speed, throttle_position, engine_load,
              coolant_temp, intake_temp, maf, distance))
        return cursor.lastrowid

def get_telemetry_history(vehicle_id, limit=1000):
    """Obtiene el historial de telemetría de un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, rpm, speed, throttle_position, engine_load,
                   coolant_temp, intake_temp, maf, distance
            FROM telemetry_data
            WHERE vehicle_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (vehicle_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_recent_telemetry(vehicle_id, minutes=60):
    """Obtiene telemetría reciente (últimos N minutos)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, rpm, speed, throttle_position, engine_load,
                   coolant_temp, intake_temp, maf, distance
            FROM telemetry_data
            WHERE vehicle_id = ?
            AND datetime(timestamp) >= datetime('now', '-' || ? || ' minutes')
            ORDER BY timestamp DESC
        ''', (vehicle_id, minutes))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_old_telemetry(days=30):
    """Elimina telemetría antigua (optimización de espacio)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM telemetry_data
            WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
        ''', (days,))
        deleted = cursor.rowcount
        print(f"[DATABASE] Eliminados {deleted} registros antiguos de telemetría")
        return deleted

# =============================================================================
# OPERACIONES - MANTENIMIENTO
# =============================================================================

def save_maintenance(vehicle_id, maintenance_type, maintenance_date, notes=None):
    """Guarda un registro de mantenimiento"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_records
            (vehicle_id, maintenance_type, maintenance_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (vehicle_id, maintenance_type, maintenance_date, notes))
        return cursor.lastrowid

def get_maintenance_history(vehicle_id):
    """Obtiene el historial de mantenimiento de un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, maintenance_type, maintenance_date, notes, created_at
            FROM maintenance_records
            WHERE vehicle_id = ?
            ORDER BY maintenance_date DESC
        ''', (vehicle_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_maintenance_record(record_id):
    """Elimina un registro de mantenimiento"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM maintenance_records WHERE id = ?', (record_id,))
        return cursor.rowcount > 0

# =============================================================================
# OPERACIONES - ANÁLISIS IA
# =============================================================================

def save_ai_analysis(vehicle_id, health_score, engine_health, thermal_health,
                     efficiency_health, predictions, warnings):
    """Guarda un análisis de IA"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Convertir listas a JSON strings
        predictions_json = json.dumps(predictions) if isinstance(predictions, list) else predictions
        warnings_json = json.dumps(warnings) if isinstance(warnings, list) else warnings

        cursor.execute('''
            INSERT INTO ai_analysis
            (vehicle_id, health_score, engine_health, thermal_health,
             efficiency_health, predictions, warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, health_score, engine_health, thermal_health,
              efficiency_health, predictions_json, warnings_json))
        return cursor.lastrowid

def get_ai_analysis_history(vehicle_id, limit=50):
    """Obtiene el historial de análisis de IA de un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, analysis_date, health_score, engine_health,
                   thermal_health, efficiency_health, predictions, warnings
            FROM ai_analysis
            WHERE vehicle_id = ?
            ORDER BY analysis_date DESC
            LIMIT ?
        ''', (vehicle_id, limit))
        rows = cursor.fetchall()

        # Convertir JSON strings de vuelta a objetos
        results = []
        for row in rows:
            data = dict(row)
            data['predictions'] = json.loads(data['predictions']) if data['predictions'] else []
            data['warnings'] = json.loads(data['warnings']) if data['warnings'] else []
            results.append(data)

        return results

def get_latest_ai_analysis(vehicle_id):
    """Obtiene el análisis más reciente de un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, analysis_date, health_score, engine_health,
                   thermal_health, efficiency_health, predictions, warnings
            FROM ai_analysis
            WHERE vehicle_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        ''', (vehicle_id,))
        row = cursor.fetchone()

        if row:
            data = dict(row)
            data['predictions'] = json.loads(data['predictions']) if data['predictions'] else []
            data['warnings'] = json.loads(data['warnings']) if data['warnings'] else []
            return data
        return None

# =============================================================================
# ESTADÍSTICAS Y UTILIDADES
# =============================================================================

def get_vehicle_statistics(vehicle_id):
    """Obtiene estadísticas generales de un vehículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Contar registros de telemetría
        cursor.execute('''
            SELECT COUNT(*) as telemetry_count,
                   MIN(timestamp) as first_reading,
                   MAX(timestamp) as last_reading
            FROM telemetry_data
            WHERE vehicle_id = ?
        ''', (vehicle_id,))
        telemetry_stats = dict(cursor.fetchone())

        # Contar registros de mantenimiento
        cursor.execute('''
            SELECT COUNT(*) as maintenance_count
            FROM maintenance_records
            WHERE vehicle_id = ?
        ''', (vehicle_id,))
        maintenance_stats = dict(cursor.fetchone())

        # Último análisis de salud
        cursor.execute('''
            SELECT health_score, analysis_date
            FROM ai_analysis
            WHERE vehicle_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        ''', (vehicle_id,))
        health_row = cursor.fetchone()
        health_stats = dict(health_row) if health_row else {'health_score': None, 'analysis_date': None}

        return {
            **telemetry_stats,
            **maintenance_stats,
            **health_stats
        }

def backup_database(backup_path=None):
    """Crea una copia de seguridad de la base de datos"""
    if backup_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'sentinel_pro_backup_{timestamp}.db'

    import shutil
    shutil.copy2(DATABASE_NAME, backup_path)
    print(f"[DATABASE] ✓ Backup creado: {backup_path}")
    return backup_path

# =============================================================================
# INICIALIZACIÓN AUTOMÁTICA
# =============================================================================

if __name__ == "__main__":
    print("Inicializando base de datos SENTINEL PRO...")
    initialize_database()
    print("✓ Listo para usar")
