# =============================================================================
# SENTINEL PRO - SCRIPT DE MIGRACIÓN DE DATOS JSON A SQLite
# Migra datos históricos de JSON a la base de datos con backup automático
# =============================================================================

import os
import json
import shutil
import database
from datetime import datetime

# Archivos JSON a migrar
HEALTH_HISTORY_FILE = 'health_history.json'
TRIP_HISTORY_FILE = 'historial_viajes.json'

def create_backup_folder():
    """Crea carpeta de backup con timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join('backup', timestamp)
    os.makedirs(backup_folder, exist_ok=True)
    return backup_folder

def backup_json_files(backup_folder):
    """Copia archivos JSON al backup"""
    backed_up_files = []

    for filename in [HEALTH_HISTORY_FILE, TRIP_HISTORY_FILE]:
        if os.path.exists(filename):
            destination = os.path.join(backup_folder, filename)
            shutil.copy2(filename, destination)
            backed_up_files.append(filename)
            print(f"[BACKUP] ✓ Copiado: {filename}")
        else:
            print(f"[BACKUP] ⚠️  No encontrado: {filename}")

    return backed_up_files

def load_json_file(filename):
    """Carga un archivo JSON"""
    if not os.path.exists(filename):
        return None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"[ERROR] No se pudo leer {filename}: {e}")
        return None

def create_default_vehicle():
    """Crea un vehículo por defecto para los datos históricos"""
    try:
        # Verificar si ya existe algún vehículo
        vehicles = database.get_all_vehicles()
        if vehicles:
            print(f"[MIGRATE] Ya existe(n) {len(vehicles)} vehículo(s) en la base de datos")
            return vehicles[0]['id']

        # Crear vehículo por defecto
        vehicle_id = database.create_vehicle(
            brand="Mi Vehículo",
            model="Datos Migrados",
            year=2020,
            mileage=100000,
            fuel_type="gasolina",
            vin=None,
            plate=None
        )

        print(f"[MIGRATE] ✓ Vehículo por defecto creado (ID: {vehicle_id})")
        return vehicle_id

    except Exception as e:
        print(f"[ERROR] Error creando vehículo por defecto: {e}")
        raise

def migrate_health_history(vehicle_id, health_data):
    """Migra datos de health_history.json a la tabla ai_analysis"""
    if not health_data:
        return 0

    count = 0
    try:
        for entry in health_data:
            try:
                # Extraer datos del análisis
                overall_score = entry.get('overall_score', 100)
                engine_health = entry.get('engine_health', 100)
                thermal_health = entry.get('thermal_health', 100)
                efficiency_health = entry.get('efficiency_health', 100)
                predictions = entry.get('predictions', [])
                warnings = entry.get('warnings', [])

                # Guardar en la base de datos
                database.save_ai_analysis(
                    vehicle_id=vehicle_id,
                    health_score=overall_score,
                    engine_health=engine_health,
                    thermal_health=thermal_health,
                    efficiency_health=efficiency_health,
                    predictions=predictions,
                    warnings=warnings
                )

                count += 1

            except Exception as e:
                print(f"[WARNING] Error migrando registro de salud: {e}")
                continue

        print(f"[MIGRATE] ✓ Migrados {count} registros de salud")
        return count

    except Exception as e:
        print(f"[ERROR] Error en migración de salud: {e}")
        return count

def migrate_trip_history(vehicle_id, trip_data):
    """Migra datos de historial_viajes.json"""
    if not trip_data:
        return 0

    # Nota: La tabla 'trips' no existe en el esquema actual de database.py
    # Los datos de viajes se pueden guardar como telemetría o crear una tabla nueva
    # Por ahora, solo contamos los registros

    count = len(trip_data) if isinstance(trip_data, list) else 0
    print(f"[MIGRATE] ℹ️  Encontrados {count} registros de viajes")
    print(f"[MIGRATE] ⚠️  La tabla 'trips' no está implementada aún")
    print(f"[MIGRATE] ℹ️  Los datos de viajes se mantendrán en el archivo JSON")

    return count

def generate_migration_report(backup_folder, stats):
    """Genera reporte de migración"""
    report_path = os.path.join(backup_folder, 'migration_report.txt')

    report = f"""
═══════════════════════════════════════════════════════════════
SENTINEL PRO - REPORTE DE MIGRACIÓN DE DATOS
═══════════════════════════════════════════════════════════════

Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ARCHIVOS RESPALDADOS:
{chr(10).join(f"  ✓ {f}" for f in stats['backed_up_files']) if stats['backed_up_files'] else "  (ninguno)"}

VEHÍCULO CREADO/UTILIZADO:
  ID: {stats['vehicle_id']}
  Marca: {stats['vehicle_brand']}
  Modelo: {stats['vehicle_model']}

REGISTROS MIGRADOS:
  • Análisis de Salud: {stats['health_records']} registros
  • Viajes: {stats['trip_records']} registros encontrados (pendiente implementar tabla)

ERRORES/ADVERTENCIAS:
{chr(10).join(f"  ⚠️  {w}" for w in stats['warnings']) if stats['warnings'] else "  (ninguno)"}

UBICACIÓN DEL BACKUP:
  {os.path.abspath(backup_folder)}

ESTADO FINAL:
  ✅ Migración completada exitosamente

═══════════════════════════════════════════════════════════════
NOTAS IMPORTANTES:
  - Los archivos JSON originales NO han sido eliminados
  - Puedes encontrar las copias de seguridad en la carpeta 'backup'
  - La base de datos se encuentra en: sentinel_pro.db
═══════════════════════════════════════════════════════════════
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[REPORT] ✓ Reporte generado: {report_path}")
    return report_path

def main():
    print("=" * 70)
    print("SENTINEL PRO - MIGRACIÓN DE DATOS JSON A SQLite")
    print("=" * 70)
    print()

    # Estadísticas de migración
    stats = {
        'backed_up_files': [],
        'vehicle_id': None,
        'vehicle_brand': '',
        'vehicle_model': '',
        'health_records': 0,
        'trip_records': 0,
        'warnings': []
    }

    try:
        # PASO 1: Crear carpeta de backup
        print("[PASO 1] Creando carpeta de backup...")
        backup_folder = create_backup_folder()
        print(f"✓ Carpeta creada: {backup_folder}")
        print()

        # PASO 2: Backup de archivos JSON
        print("[PASO 2] Respaldando archivos JSON...")
        stats['backed_up_files'] = backup_json_files(backup_folder)
        print()

        # PASO 3: Cargar archivos JSON
        print("[PASO 3] Cargando archivos JSON...")
        health_data = load_json_file(HEALTH_HISTORY_FILE)
        trip_data = load_json_file(TRIP_HISTORY_FILE)

        if health_data:
            print(f"✓ {HEALTH_HISTORY_FILE}: {len(health_data)} registros")
        else:
            print(f"⚠️  {HEALTH_HISTORY_FILE}: No encontrado o vacío")
            stats['warnings'].append(f"{HEALTH_HISTORY_FILE} no encontrado")

        if trip_data:
            print(f"✓ {TRIP_HISTORY_FILE}: {len(trip_data)} registros")
        else:
            print(f"⚠️  {TRIP_HISTORY_FILE}: No encontrado o vacío")
            stats['warnings'].append(f"{TRIP_HISTORY_FILE} no encontrado")
        print()

        # PASO 4: Crear/obtener vehículo
        print("[PASO 4] Preparando vehículo destino...")
        vehicle_id = create_default_vehicle()
        stats['vehicle_id'] = vehicle_id

        # Obtener datos del vehículo
        vehicle = database.get_vehicle_by_id(vehicle_id)
        if vehicle:
            stats['vehicle_brand'] = vehicle['brand']
            stats['vehicle_model'] = vehicle['model']
        print()

        # PASO 5: Migrar datos de salud
        print("[PASO 5] Migrando datos de salud...")
        stats['health_records'] = migrate_health_history(vehicle_id, health_data)
        print()

        # PASO 6: Procesar datos de viajes
        print("[PASO 6] Procesando datos de viajes...")
        stats['trip_records'] = migrate_trip_history(vehicle_id, trip_data)
        print()

        # PASO 7: Generar reporte
        print("[PASO 7] Generando reporte de migración...")
        report_path = generate_migration_report(backup_folder, stats)
        print()

        # RESUMEN FINAL
        print("=" * 70)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print()
        print("RESUMEN:")
        print(f"  • Vehículo ID: {stats['vehicle_id']}")
        print(f"  • Registros de salud migrados: {stats['health_records']}")
        print(f"  • Registros de viajes encontrados: {stats['trip_records']}")
        print(f"  • Backup ubicado en: {os.path.abspath(backup_folder)}")
        print()
        print("PRÓXIMOS PASOS:")
        print("  1. Revisa el reporte: migration_report.txt")
        print("  2. Los archivos JSON originales NO han sido eliminados")
        print("  3. Puedes iniciar el servidor: python obd_server.py")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR EN LA MIGRACIÓN")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
