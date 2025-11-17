# =============================================================================
# SENTINEL PRO - MANTENIMIENTO PREDICTIVO v10.0 - MULTI-VEHÍCULO + SQLite
# Sistema completo con gestión de múltiples vehículos
# =============================================================================
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import obd
import time
import json
import requests
import geocoder
import google.generativeai as genai
from fpdf import FPDF
import os
import traceback
import re
import csv
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import statistics

# Importar módulo de base de datos
import database

# ----- CONFIGURACIÓN OBLIGATORIA -----
OBD_PORT = "COM6"  # CAMBIA ESTO A TU PUERTO
GEMINI_API_KEY = "AIzaSyDMtGE41CV8SbFzmWG8a6oPQgVf58k8HLE"  # TU API KEY
GEMINI_MODEL_NAME = "models/gemini-pro-latest"
# -------------------------------------

# Configuración de archivos
CSV_FOLDER = 'csv_data'
UPLOAD_FOLDER = 'uploaded_csv'
ALLOWED_EXTENSIONS = {'csv'}
CSV_FILENAME = os.path.join(CSV_FOLDER, 'obd_readings.csv')
HEALTH_HISTORY_FILE = 'health_history.json'
TRIP_HISTORY_FILE = 'historial_viajes.json'

os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Variables globales
connection = None
supported_commands_cache = set()
last_connection_attempt_time = 0
last_thermal_reading_time = 0
RECONNECTION_COOLDOWN = 10
THERMAL_READING_INTERVAL = 60

# NUEVO: Variable para vehículo activo
active_vehicle_id = None

trip_data = {}
maintenanceHistory = []

vehicle_health = {
    "overall_score": 100,
    "engine_health": 100,
    "thermal_health": 100,
    "efficiency_health": 100,
    "warnings": [],
    "predictions": [],
    "last_update": None
}

# Inicialización Gemini
model = None
try:
    if "TU_API_KEY" in GEMINI_API_KEY or len(GEMINI_API_KEY) < 30:
        raise ValueError("API KEY no válida")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    print(f"[GEMINI] ✓ Configurado: {GEMINI_MODEL_NAME}")
except Exception as e:
    print(f"[GEMINI] ✗ Error: {e}")

# Inicializar base de datos al inicio
try:
    database.initialize_database()
    print("[DATABASE] ✓ Base de datos inicializada")
except Exception as e:
    print(f"[DATABASE] ✗ Error: {e}")

# =============================================================================
# ENDPOINTS - GESTIÓN DE VEHÍCULOS
# =============================================================================

@app.route("/api/vehicles", methods=["POST"])
def create_vehicle():
    """Crear un nuevo vehículo"""
    try:
        data = request.json
        brand = data.get('brand')
        model = data.get('model')
        year = data.get('year')
        mileage = data.get('mileage')
        fuel_type = data.get('fuel_type', 'gasolina')
        vin = data.get('vin')
        plate = data.get('plate')

        if not all([brand, model, year, mileage]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        vehicle_id = database.create_vehicle(
            brand, model, int(year), int(mileage), fuel_type, vin, plate
        )

        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "message": "Vehículo creado correctamente"
        }), 201

    except Exception as e:
        print(f"[VEHICLES] Error creando vehículo: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    """Obtener todos los vehículos"""
    try:
        vehicles = database.get_all_vehicles()

        # Añadir estadísticas a cada vehículo
        for vehicle in vehicles:
            stats = database.get_vehicle_statistics(vehicle['id'])
            vehicle['statistics'] = stats

        return jsonify({
            "success": True,
            "vehicles": vehicles
        })

    except Exception as e:
        print(f"[VEHICLES] Error obteniendo vehículos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles/<int:vehicle_id>", methods=["GET"])
def get_vehicle(vehicle_id):
    """Obtener un vehículo específico"""
    try:
        vehicle = database.get_vehicle_by_id(vehicle_id)

        if not vehicle:
            return jsonify({"error": "Vehículo no encontrado"}), 404

        # Añadir estadísticas
        stats = database.get_vehicle_statistics(vehicle_id)
        vehicle['statistics'] = stats

        return jsonify({
            "success": True,
            "vehicle": vehicle
        })

    except Exception as e:
        print(f"[VEHICLES] Error obteniendo vehículo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles/<int:vehicle_id>", methods=["PUT"])
def update_vehicle(vehicle_id):
    """Actualizar un vehículo existente"""
    try:
        data = request.json
        brand = data.get('brand')
        model = data.get('model')
        year = data.get('year')
        mileage = data.get('mileage')
        fuel_type = data.get('fuel_type', 'gasolina')
        vin = data.get('vin')
        plate = data.get('plate')

        if not all([brand, model, year, mileage]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        success = database.update_vehicle(
            vehicle_id, brand, model, int(year), int(mileage), fuel_type, vin, plate
        )

        if not success:
            return jsonify({"error": "Vehículo no encontrado"}), 404

        return jsonify({
            "success": True,
            "message": "Vehículo actualizado correctamente"
        })

    except Exception as e:
        print(f"[VEHICLES] Error actualizando vehículo: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles/<int:vehicle_id>", methods=["DELETE"])
def delete_vehicle(vehicle_id):
    """Eliminar un vehículo"""
    global active_vehicle_id

    try:
        # Si es el vehículo activo, deseleccionarlo
        if active_vehicle_id == vehicle_id:
            active_vehicle_id = None

        success = database.delete_vehicle(vehicle_id)

        if not success:
            return jsonify({"error": "Vehículo no encontrado"}), 404

        return jsonify({
            "success": True,
            "message": "Vehículo eliminado correctamente"
        })

    except Exception as e:
        print(f"[VEHICLES] Error eliminando vehículo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles/<int:vehicle_id>/select", methods=["POST"])
def select_vehicle(vehicle_id):
    """Seleccionar vehículo activo para monitoreo"""
    global active_vehicle_id

    try:
        # Verificar que el vehículo existe
        vehicle = database.get_vehicle_by_id(vehicle_id)

        if not vehicle:
            return jsonify({"error": "Vehículo no encontrado"}), 404

        active_vehicle_id = vehicle_id

        # Resetear datos de viaje al cambiar de vehículo
        reset_trip()

        print(f"[VEHICLES] Vehículo activo: {vehicle['brand']} {vehicle['model']}")

        return jsonify({
            "success": True,
            "active_vehicle_id": active_vehicle_id,
            "vehicle": vehicle,
            "message": f"Vehículo {vehicle['brand']} {vehicle['model']} seleccionado"
        })

    except Exception as e:
        print(f"[VEHICLES] Error seleccionando vehículo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vehicles/active", methods=["GET"])
def get_active_vehicle():
    """Obtener el vehículo actualmente activo"""
    global active_vehicle_id

    if active_vehicle_id is None:
        return jsonify({
            "success": True,
            "active_vehicle_id": None,
            "message": "No hay vehículo activo"
        })

    try:
        vehicle = database.get_vehicle_by_id(active_vehicle_id)

        if not vehicle:
            active_vehicle_id = None
            return jsonify({
                "success": True,
                "active_vehicle_id": None,
                "message": "Vehículo activo no encontrado"
            })

        return jsonify({
            "success": True,
            "active_vehicle_id": active_vehicle_id,
            "vehicle": vehicle
        })

    except Exception as e:
        print(f"[VEHICLES] Error obteniendo vehículo activo: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# ENDPOINTS - TELEMETRÍA
# =============================================================================

@app.route("/api/telemetry/<int:vehicle_id>", methods=["GET"])
def get_telemetry_history(vehicle_id):
    """Obtener historial de telemetría de un vehículo"""
    try:
        limit = request.args.get('limit', 1000, type=int)
        telemetry = database.get_telemetry_history(vehicle_id, limit)

        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "count": len(telemetry),
            "telemetry": telemetry
        })

    except Exception as e:
        print(f"[TELEMETRY] Error obteniendo historial: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# ENDPOINTS - MANTENIMIENTO
# =============================================================================

@app.route("/api/maintenance", methods=["POST"])
def create_maintenance_record():
    """Guardar un registro de mantenimiento"""
    try:
        data = request.json
        vehicle_id = data.get('vehicle_id')
        maintenance_type = data.get('maintenance_type')
        maintenance_date = data.get('maintenance_date')
        notes = data.get('notes')

        if not all([vehicle_id, maintenance_type, maintenance_date]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        record_id = database.save_maintenance(
            vehicle_id, maintenance_type, maintenance_date, notes
        )

        return jsonify({
            "success": True,
            "record_id": record_id,
            "message": "Registro de mantenimiento guardado"
        }), 201

    except Exception as e:
        print(f"[MAINTENANCE] Error guardando registro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/maintenance/<int:vehicle_id>", methods=["GET"])
def get_maintenance_history_endpoint(vehicle_id):
    """Obtener historial de mantenimiento de un vehículo"""
    try:
        maintenance = database.get_maintenance_history(vehicle_id)

        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "count": len(maintenance),
            "maintenance": maintenance
        })

    except Exception as e:
        print(f"[MAINTENANCE] Error obteniendo historial: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/maintenance/<int:record_id>", methods=["DELETE"])
def delete_maintenance_record_endpoint(record_id):
    """Eliminar un registro de mantenimiento"""
    try:
        success = database.delete_maintenance_record(record_id)

        if not success:
            return jsonify({"error": "Registro no encontrado"}), 404

        return jsonify({
            "success": True,
            "message": "Registro eliminado"
        })

    except Exception as e:
        print(f"[MAINTENANCE] Error eliminando registro: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# ENDPOINTS - ANÁLISIS IA
# =============================================================================

@app.route("/api/analysis", methods=["POST"])
def save_analysis():
    """Guardar análisis de IA"""
    try:
        data = request.json
        vehicle_id = data.get('vehicle_id')
        health_score = data.get('health_score')
        engine_health = data.get('engine_health')
        thermal_health = data.get('thermal_health')
        efficiency_health = data.get('efficiency_health')
        predictions = data.get('predictions', [])
        warnings = data.get('warnings', [])

        if vehicle_id is None:
            return jsonify({"error": "vehicle_id requerido"}), 400

        analysis_id = database.save_ai_analysis(
            vehicle_id, health_score, engine_health, thermal_health,
            efficiency_health, predictions, warnings
        )

        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "message": "Análisis guardado"
        }), 201

    except Exception as e:
        print(f"[ANALYSIS] Error guardando análisis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/analysis/<int:vehicle_id>", methods=["GET"])
def get_analysis_history_endpoint(vehicle_id):
    """Obtener historial de análisis de un vehículo"""
    try:
        limit = request.args.get('limit', 50, type=int)
        analysis = database.get_ai_analysis_history(vehicle_id, limit)

        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "count": len(analysis),
            "analysis": analysis
        })

    except Exception as e:
        print(f"[ANALYSIS] Error obteniendo historial: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# FUNCIONES CSV (mantenidas para compatibilidad)
# =============================================================================

def initialize_csv():
    if not os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'date', 'time', 'vehicle_id',
                'rpm', 'speed_kmh', 'throttle_pos', 'engine_load', 'maf',
                'coolant_temp', 'intake_temp', 'distance_km'
            ])
        print(f"[CSV] ✓ Archivo creado con columnas optimizadas")

def save_reading_to_csv(data, thermal_data=None, vehicle_id=None):
    try:
        now = datetime.now()
        with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                now.isoformat(),
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                vehicle_id if vehicle_id else '',
                data.get('RPM', ''),
                data.get('SPEED', ''),
                data.get('THROTTLE_POS', ''),
                data.get('ENGINE_LOAD', ''),
                data.get('MAF', ''),
                thermal_data.get('COOLANT_TEMP', '') if thermal_data else '',
                thermal_data.get('INTAKE_TEMP', '') if thermal_data else '',
                data.get('total_distance', '')
            ])
    except Exception as e:
        print(f"[CSV] Error guardando: {e}")

def read_csv_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"[CSV] Error leyendo: {e}")
        return []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# CÁLCULO MEJORADO DE DISTANCIA
# =============================================================================

def calculate_distance(speed_kmh, time_delta_s):
    if speed_kmh and speed_kmh > 0 and time_delta_s > 0:
        distance_km = (speed_kmh / 3600) * time_delta_s
        return distance_km
    return 0

# =============================================================================
# ANÁLISIS DE SALUD DEL VEHÍCULO (modificado para guardar en DB)
# =============================================================================

def analyze_vehicle_health(trip_points):
    global vehicle_health, active_vehicle_id

    if not trip_points or len(trip_points) < 10:
        return vehicle_health

    try:
        rpms = [p.get('RPM', 0) for p in trip_points if p.get('RPM') and p.get('RPM') > 0]
        throttles = [p.get('THROTTLE_POS', 0) for p in trip_points if p.get('THROTTLE_POS') is not None]
        loads = [p.get('ENGINE_LOAD', 0) for p in trip_points if p.get('ENGINE_LOAD') is not None]
        mafs = [p.get('MAF', 0) for p in trip_points if p.get('MAF') and p.get('MAF') > 0]
        temps_coolant = [p.get('COOLANT_TEMP', 0) for p in trip_points if p.get('COOLANT_TEMP') and p.get('COOLANT_TEMP') > 0]
        temps_intake = [p.get('INTAKE_TEMP', 0) for p in trip_points if p.get('INTAKE_TEMP') and p.get('INTAKE_TEMP') > 0]

        warnings = []
        predictions = []

        # 1. SALUD DEL MOTOR
        engine_health = 100
        if rpms:
            rpm_avg = statistics.mean(rpms)
            rpm_max = max(rpms)

            high_rpm_count = sum(1 for r in rpms if r > 4000)
            high_rpm_ratio = high_rpm_count / len(rpms)

            if high_rpm_ratio > 0.3:
                engine_health -= 20
                warnings.append("⚠️ Uso frecuente de RPM altas (>4000). Aumenta desgaste del motor.")
                predictions.append("Riesgo medio de desgaste prematuro de componentes en 12-18 meses")

            if rpm_max > 6000:
                engine_health -= 15
                warnings.append("🔴 RPM CRÍTICAS detectadas (>6000). Revisar limitador.")

        if loads:
            load_avg = statistics.mean(loads)
            if load_avg > 80:
                engine_health -= 10
                warnings.append("⚠️ Carga motor alta (>80%). Revisar admisión.")

        # 2. SALUD TÉRMICA
        thermal_health = 100
        if temps_coolant:
            temp_max = max(temps_coolant)
            temp_avg = statistics.mean(temps_coolant)

            if temp_max > 105:
                thermal_health -= 30
                warnings.append("🔴 CRÍTICO: Temperatura >105°C. Revisar sistema URGENTE.")
                predictions.append("Riesgo ALTO de fallo en junta culata o radiador en 1-3 meses")
            elif temp_avg > 95:
                thermal_health -= 15
                warnings.append("⚠️ Temperatura elevada. Revisar termostato y radiador.")
                predictions.append("Riesgo medio de sobrecalentamiento. Mantenimiento en 3-6 meses")

        if temps_intake:
            temp_intake_avg = statistics.mean(temps_intake)
            if temp_intake_avg > 50:
                thermal_health -= 10
                warnings.append("⚠️ Temperatura admisión alta. Revisar intercooler.")

        # 3. EFICIENCIA
        efficiency_health = 100
        if mafs:
            maf_avg = statistics.mean(mafs)
            if maf_avg < 10 or maf_avg > 80:
                efficiency_health -= 15
                warnings.append("⚠️ Flujo aire anómalo. Revisar MAF y filtro.")
                predictions.append("Posible obstrucción en admisión. Reducción eficiencia 5-10%")

        if throttles and len(throttles) > 1:
            harsh_accel = 0
            for i in range(1, len(throttles)):
                if throttles[i] - throttles[i-1] > 30:
                    harsh_accel += 1

            harsh_ratio = harsh_accel / len(throttles)
            if harsh_ratio > 0.05:
                efficiency_health -= 10
                warnings.append("⚠️ Conducción agresiva. Aumenta consumo y desgaste.")

        # PUNTUACIÓN GLOBAL
        overall_score = round((engine_health + thermal_health + efficiency_health) / 3)

        vehicle_health = {
            "overall_score": overall_score,
            "engine_health": round(engine_health),
            "thermal_health": round(thermal_health),
            "efficiency_health": round(efficiency_health),
            "warnings": warnings,
            "predictions": predictions,
            "last_update": datetime.now().isoformat()
        }

        # Guardar en base de datos si hay vehículo activo
        if active_vehicle_id:
            try:
                database.save_ai_analysis(
                    active_vehicle_id,
                    vehicle_health['overall_score'],
                    vehicle_health['engine_health'],
                    vehicle_health['thermal_health'],
                    vehicle_health['efficiency_health'],
                    vehicle_health['predictions'],
                    vehicle_health['warnings']
                )
            except Exception as e:
                print(f"[HEALTH] Error guardando en DB: {e}")

        save_health_history(vehicle_health)
        return vehicle_health

    except Exception as e:
        print(f"[HEALTH] Error en análisis: {e}")
        return vehicle_health

def save_health_history(health_data):
    try:
        history = []
        if os.path.exists(HEALTH_HISTORY_FILE):
            with open(HEALTH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)

        history.append(health_data)

        if len(history) > 100:
            history = history[-100:]

        with open(HEALTH_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[HEALTH] Error guardando: {e}")

def get_trip_history():
    if os.path.exists(TRIP_HISTORY_FILE):
        with open(TRIP_HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_trip_summary(summary):
    history = get_trip_history()
    history.append(summary)
    with open(TRIP_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# =============================================================================
# FUNCIONES OBD
# =============================================================================

def initialize_obd_connection(force_reconnect=False):
    global connection, supported_commands_cache, last_connection_attempt_time

    current_time = time.time()
    if not force_reconnect and current_time - last_connection_attempt_time < RECONNECTION_COOLDOWN:
        return False

    last_connection_attempt_time = current_time

    if connection and connection.is_connected() and not force_reconnect:
        return True

    try:
        print(f"[OBD] Conectando a {OBD_PORT}...")
        new_connection = obd.OBD(OBD_PORT, baudrate=None, fast=False, timeout=10)

        if new_connection.is_connected():
            connection = new_connection
            print("[OBD] ✓ Conectado exitosamente")
            time.sleep(1)

            if force_reconnect or not supported_commands_cache:
                supported_commands_cache = set(connection.supported_commands)

            if supported_commands_cache:
                print(f"[OBD] ✓ {len(supported_commands_cache)} comandos soportados")
            return True
        else:
            print(f"[OBD] ✗ No se pudo conectar")
            connection = None
            return False

    except Exception as e:
        print(f"[OBD] ✗ Error: {e}")
        connection = None
        return False

def reset_trip():
    global trip_data
    trip_data = {
        "active": False,
        "start_time": None,
        "last_read_time": None,
        "distance_km": 0.0,
        "points": []
    }

reset_trip()
initialize_csv()

# =============================================================================
# ENDPOINTS OBD (modificados para multi-vehículo)
# =============================================================================

@app.route("/get_live_data", methods=["GET"])
def get_live_data():
    global connection, trip_data, last_thermal_reading_time, active_vehicle_id

    if not connection or not connection.is_connected():
        if not initialize_obd_connection(force_reconnect=True):
            return jsonify({
                "offline": True,
                "RPM": None,
                "SPEED": None,
                "THROTTLE_POS": None,
                "ENGINE_LOAD": None,
                "MAF": None,
                "COOLANT_TEMP": None,
                "INTAKE_TEMP": None,
                "total_distance": 0,
                "active_vehicle_id": active_vehicle_id
            })

    # DATOS CRÍTICOS (cada 3s)
    critical_commands = [
        obd.commands.RPM,
        obd.commands.SPEED,
        obd.commands.THROTTLE_POS,
        obd.commands.ENGINE_LOAD,
        obd.commands.MAF
    ]

    results = {}
    for cmd in critical_commands:
        try:
            response = connection.query(cmd)
            if response and response.value is not None:
                results[cmd.name] = response.value.magnitude if hasattr(response.value, 'magnitude') else response.value
            else:
                results[cmd.name] = None
        except Exception as e:
            results[cmd.name] = None

    # DATOS TÉRMICOS (cada 60s)
    thermal_data = {}
    current_time = time.time()

    if current_time - last_thermal_reading_time >= THERMAL_READING_INTERVAL:
        thermal_commands = [
            obd.commands.COOLANT_TEMP,
            obd.commands.INTAKE_TEMP
        ]

        for cmd in thermal_commands:
            try:
                response = connection.query(cmd)
                if response and response.value is not None:
                    thermal_data[cmd.name] = response.value.magnitude if hasattr(response.value, 'magnitude') else response.value
                else:
                    thermal_data[cmd.name] = None
            except Exception as e:
                thermal_data[cmd.name] = None

        last_thermal_reading_time = current_time
        results.update(thermal_data)
    else:
        if trip_data.get("points") and len(trip_data["points"]) > 0:
            last_point = trip_data["points"][-1]
            results['COOLANT_TEMP'] = last_point.get('COOLANT_TEMP')
            results['INTAKE_TEMP'] = last_point.get('INTAKE_TEMP')
        else:
            results['COOLANT_TEMP'] = None
            results['INTAKE_TEMP'] = None

    # GESTIÓN DE VIAJE
    if results.get("RPM") and results.get("RPM") > 400:
        if not trip_data["active"]:
            reset_trip()
            trip_data["active"] = True
            trip_data["start_time"] = time.time()
            trip_data["last_read_time"] = time.time()
            print("[TRIP] ✓ Nuevo viaje iniciado")

        current_time = time.time()
        time_delta_s = current_time - trip_data["last_read_time"]

        if results.get("SPEED") and time_delta_s > 0:
            distance_increment = calculate_distance(results.get("SPEED"), time_delta_s)
            trip_data["distance_km"] += distance_increment

        results['total_distance'] = round(trip_data['distance_km'], 3)
        trip_data["points"].append(results)
        trip_data["last_read_time"] = current_time

        # Guardar en CSV y en base de datos
        save_reading_to_csv(results, thermal_data if thermal_data else None, active_vehicle_id)

        # Guardar en base de datos si hay vehículo activo
        if active_vehicle_id:
            try:
                database.save_telemetry(
                    active_vehicle_id,
                    results.get('RPM'),
                    results.get('SPEED'),
                    results.get('THROTTLE_POS'),
                    results.get('ENGINE_LOAD'),
                    results.get('COOLANT_TEMP'),
                    results.get('INTAKE_TEMP'),
                    results.get('MAF'),
                    results.get('total_distance')
                )
            except Exception as e:
                print(f"[TELEMETRY] Error guardando en DB: {e}")

        if len(trip_data["points"]) % 30 == 0:
            analyze_vehicle_health(trip_data["points"])
    else:
        results['total_distance'] = trip_data['distance_km'] if trip_data["active"] else 0

    results['active_vehicle_id'] = active_vehicle_id
    return jsonify(results)

@app.route("/get_vehicle_health", methods=["GET"])
def get_vehicle_health():
    global vehicle_health
    return jsonify(vehicle_health)

@app.route("/get_health_history", methods=["GET"])
def get_health_history():
    try:
        if os.path.exists(HEALTH_HISTORY_FILE):
            with open(HEALTH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return jsonify({"history": history})
        return jsonify({"history": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predictive_analysis", methods=["POST"])
def predictive_analysis():
    global model, trip_data

    if not model:
        return jsonify({"error": "IA no configurada"}), 500

    vehicle_info = request.json.get("vehicleInfo", {})

    if not trip_data["points"] or len(trip_data["points"]) < 20:
        return jsonify({"error": "Datos insuficientes. Conduce al menos 2 minutos."}), 400

    try:
        points = trip_data["points"]

        rpms = [p.get('RPM', 0) for p in points if p.get('RPM')]
        loads = [p.get('ENGINE_LOAD', 0) for p in points if p.get('ENGINE_LOAD')]
        mafs = [p.get('MAF', 0) for p in points if p.get('MAF')]
        temps = [p.get('COOLANT_TEMP', 0) for p in points if p.get('COOLANT_TEMP')]

        stats = {
            "rpm_avg": round(statistics.mean(rpms)) if rpms else 0,
            "rpm_max": round(max(rpms)) if rpms else 0,
            "load_avg": round(statistics.mean(loads)) if loads else 0,
            "maf_avg": round(statistics.mean(mafs), 2) if mafs else 0,
            "temp_max": round(max(temps)) if temps else 0,
            "distance": round(trip_data["distance_km"], 2),
            "duration_min": round((trip_data["last_read_time"] - trip_data["start_time"]) / 60, 1)
        }

        prompt = f"""Eres ingeniero de diagnóstico vehicular especializado en MANTENIMIENTO PREDICTIVO.

VEHÍCULO: {vehicle_info.get('brand', 'N/D')} {vehicle_info.get('model', 'N/D')} ({vehicle_info.get('year', 'N/D')})
KILOMETRAJE: {vehicle_info.get('mileage', 'N/D')} km

DATOS VIAJE:
- Duración: {stats['duration_min']} min
- Distancia: {stats['distance']} km
- RPM promedio: {stats['rpm_avg']} / máx: {stats['rpm_max']}
- Carga promedio: {stats['load_avg']}%
- MAF promedio: {stats['maf_avg']} g/s
- Temp máx: {stats['temp_max']}°C

Proporciona:
1. Predicción de fallos en 6-12 meses
2. Componentes prioritarios
3. Vida útil estimada
4. Mantenimiento preventivo

JSON VÁLIDO:
{{
    "predictive_score": 85,
    "risk_level": "Bajo",
    "predictions": [
        {{
            "component": "Bomba agua",
            "failure_probability": "15%",
            "estimated_timeframe": "12-18 meses",
            "symptoms": "Temp elevada ocasional",
            "action": "Inspeccionar próxima revisión"
        }}
    ],
    "priority_maintenance": [
        {{
            "task": "Cambio aceite",
            "urgency": "Alta",
            "timeframe": "1000km",
            "reason": "Kilometraje alto"
        }}
    ],
    "component_health": {{
        "engine": "85%",
        "cooling_system": "90%",
        "air_intake": "88%"
    }},
    "cost_estimate": {{
        "preventive_now": "150-300€",
        "if_delayed": "800-1500€"
    }}
}}"""

        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()

        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            ai_analysis = json.loads(json_match.group())
        else:
            ai_analysis = json.loads(cleaned)

        ai_analysis["trip_stats"] = stats
        ai_analysis["vehicle_health"] = vehicle_health

        return jsonify(ai_analysis)

    except Exception as e:
        print(f"[PREDICTIVE] Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/get_common_failures", methods=["POST"])
def get_common_failures():
    if not model:
        return jsonify({"error": "IA no configurada"}), 500

    v = request.json.get("vehicleInfo", {})
    brand = v.get("brand")
    model_year = v.get("model")
    year = v.get("year")

    if not all([brand, model_year, year]):
        return jsonify({"error": "Marca, modelo y año requeridos."}), 400

    prompt = f"""Actúa como mecánico jefe de taller con 20 años en {brand}.

VEHÍCULO: {brand} {model_year} año {year}

Identifica las 3 averías más comunes para este modelo específico.

Responde SOLO con JSON válido:
{{
    "failures": [
        {{
            "title": "Nombre de la avería",
            "symptom": "Síntoma que presenta",
            "cause": "Causa principal",
            "solution": "Solución recomendada",
            "severity": "Alta"
        }},
        {{
            "title": "Segunda avería",
            "symptom": "Síntoma",
            "cause": "Causa",
            "solution": "Solución",
            "severity": "Media"
        }},
        {{
            "title": "Tercera avería",
            "symptom": "Síntoma",
            "cause": "Causa",
            "solution": "Solución",
            "severity": "Baja"
        }}
    ],
    "recommendation": "Consejo general de mantenimiento preventivo para este modelo"
}}"""

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

        json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
        if json_match:
            failures_data = json.loads(json_match.group())
        else:
            failures_data = json.loads(cleaned_response)

        return jsonify(failures_data)
    except Exception as e:
        print(f"[FAILURES] Error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error IA: {e}"}), 500

@app.route("/get_vehicle_valuation", methods=["POST"])
def get_vehicle_valuation():
    if not model:
        return jsonify({"error": "IA no configurada"}), 500

    v = request.json.get("vehicleInfo", {})
    brand = v.get("brand", "")
    model_year = v.get("model", "")
    year = v.get("year", "")
    mileage = v.get("mileage", "")

    if not all([brand, model_year, year, mileage]):
        return jsonify({"error": "Todos los datos requeridos."}), 400

    trip_history = get_trip_history()
    driving_style_summary = "Sin datos"
    driving_quality_score = 5

    if trip_history and len(trip_history) > 0:
        total_km = sum(t.get('distancia_km', 0) for t in trip_history)

        if total_km > 1:
            driving_quality_score = 8
            driving_style_summary = f"Conducción registrada: {len(trip_history)} viajes"

    maintenance_history = request.json.get("maintenanceHistory", [])
    maintenance_score = 5

    if maintenance_history:
        num = len(maintenance_history)
        if num >= 10:
            maintenance_score = 9
        elif num >= 5:
            maintenance_score = 8
        elif num >= 2:
            maintenance_score = 7
        else:
            maintenance_score = 6

    print(f"[VALUATION] Tasando {brand} {model_year} {year}")

    try:
        prompt = f"""Eres tasador profesional de vehículos segunda mano en España con 20 años experiencia.

VEHÍCULO: {brand} {model_year} - Año {year} - {mileage} km - {v.get('type', 'gasolina')}

CONDICIÓN:
- Conducción: {driving_style_summary} (Score: {driving_quality_score}/10)
- Mantenimiento: {len(maintenance_history)} intervenciones (Score: {maintenance_score}/10)

Proporciona tasación realista del mercado español actual, ajustada por condición del vehículo.

Responde SOLO con JSON válido:
{{
    "min_price": 8000,
    "max_price": 12000,
    "realistic_price": 10000,
    "justification": "Explicación detallada de 2-3 líneas sobre la valoración"
}}"""

        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

        json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
        if json_match:
            valuation_data = json.loads(json_match.group())
        else:
            valuation_data = json.loads(cleaned_response)

        valuation_data["min_price"] = int(valuation_data["min_price"])
        valuation_data["max_price"] = int(valuation_data["max_price"])
        valuation_data["realistic_price"] = int(valuation_data["realistic_price"])

        print(f"[VALUATION] ✓ {valuation_data['realistic_price']}€")
        return jsonify(valuation_data)

    except Exception as e:
        print(f"[VALUATION] Error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error: {e}"}), 500

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)

        return jsonify({
            "success": True,
            "filename": new_filename
        })

    return jsonify({"error": "Tipo no permitido"}), 400

@app.route("/list_uploaded_csvs", methods=["GET"])
def list_uploaded_csvs():
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.csv'):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                size = os.path.getsize(filepath)
                modified = os.path.getmtime(filepath)
                files.append({
                    'filename': filename,
                    'size_kb': round(size / 1024, 2),
                    'modified': datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')
                })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_current_csv", methods=["GET"])
def download_current_csv():
    if os.path.exists(CSV_FILENAME):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            CSV_FILENAME,
            as_attachment=True,
            download_name=f'sentinel_data_{timestamp}.csv'
        )
    return jsonify({"error": "No hay datos"}), 404

@app.route("/generate_report", methods=["POST"])
def generate_report():
    vehicle_info = request.json.get("vehicleInfo", {})
    health_data = vehicle_health
    maintenance = request.json.get("maintenanceHistory", [])

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, 'SENTINEL PRO - Informe Diagnostico', 0, 1, 'C')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 10, f"{vehicle_info.get('brand', 'N/D')} {vehicle_info.get('model', 'N/D')} - {vehicle_info.get('year', 'N/D')}", 0, 1, 'C')
    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Puntuacion Salud: {health_data['overall_score']}/100", 0, 1, 'L')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Sistemas:', 0, 1, 'L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"- Motor: {health_data['engine_health']}/100", 0, 1)
    pdf.cell(0, 6, f"- Termica: {health_data['thermal_health']}/100", 0, 1)
    pdf.cell(0, 6, f"- Eficiencia: {health_data['efficiency_health']}/100", 0, 1)
    pdf.ln(5)

    if health_data['warnings']:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, 'Advertencias:', 0, 1, 'L')
        pdf.set_font("Arial", '', 9)
        for w in health_data['warnings']:
            pdf.multi_cell(0, 5, f"- {w}")

    if health_data['predictions']:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, 'Predicciones:', 0, 1, 'L')
        pdf.set_font("Arial", '', 9)
        for p in health_data['predictions']:
            pdf.multi_cell(0, 5, f"- {p}")

    if maintenance:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, 'Mantenimiento:', 0, 1, 'L')
        pdf.set_font("Arial", '', 9)
        for m in maintenance[:10]:
            pdf.cell(0, 5, f"- {m.get('date', 'N/D')}: {m.get('type', 'N/D')}", 0, 1)

    filename = f"sentinel_pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)

# =============================================================================
# ENDPOINT DE BACKUP DE BASE DE DATOS
# =============================================================================

@app.route("/api/backup/database", methods=["GET"])
def backup_database_endpoint():
    """Descargar backup de la base de datos"""
    try:
        backup_path = database.backup_database()
        return send_file(backup_path, as_attachment=True)
    except Exception as e:
        print(f"[BACKUP] Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 70)
    print("SENTINEL PRO - MANTENIMIENTO PREDICTIVO v10.0 MULTI-VEHÍCULO")
    print("=" * 70)
    print(f"\n[CONFIG] Puerto OBD: {OBD_PORT}")
    print(f"[CONFIG] Modelo IA: {GEMINI_MODEL_NAME}")
    print(f"[CONFIG] Base de Datos: {database.DATABASE_NAME}")
    print("\n[CARACTERÍSTICAS]")
    print("  ✓ Gestión de múltiples vehículos")
    print("  ✓ Base de datos SQLite persistente")
    print("  ✓ Historial completo por vehículo")
    print("  ✓ Datos críticos cada 3s: RPM, velocidad, acelerador, carga, MAF")
    print("  ✓ Datos térmicos cada 60s: temperaturas refrigerante/admisión")
    print("  ✓ Cálculo preciso de distancia por integración")
    print("  ✓ Análisis salud automático cada 90s")
    print("\n[FEATURES PROFESIONALES]")
    print("  ✓ Scoring salud 0-100")
    print("  ✓ Detección patrones desgaste")
    print("  ✓ Predicción fallos con IA")
    print("  ✓ Alertas tempranas")
    print("  ✓ Averías comunes por modelo")
    print("  ✓ Tasación inteligente")
    print("  ✓ Backup de base de datos")

    initialize_obd_connection(force_reconnect=True)
    print("\n✓ Servidor activo en http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
