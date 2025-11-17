# =============================================================================
# SENTINEL PRO - SCRIPT DE INICIALIZACIÓN DE BASE DE DATOS
# Ejecuta este archivo UNA VEZ para crear la base de datos
# =============================================================================

import database
import os

def main():
    print("=" * 70)
    print("SENTINEL PRO - INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 70)
    print()

    # Verificar si ya existe la base de datos
    if os.path.exists(database.DATABASE_NAME):
        print(f"⚠️  La base de datos '{database.DATABASE_NAME}' ya existe.")
        respuesta = input("¿Deseas continuar? (se crearán las tablas si faltan) [S/n]: ")
        if respuesta.lower() == 'n':
            print("❌ Operación cancelada.")
            return

    print("[PASO 1] Creando base de datos y tablas...")
    try:
        database.initialize_database()
        print("✓ Base de datos creada correctamente")
    except Exception as e:
        print(f"❌ Error al crear base de datos: {e}")
        return

    print()
    print("[PASO 2] Verificando estructura...")

    # Obtener información sobre las tablas creadas
    try:
        vehicles = database.get_all_vehicles()
        print(f"✓ Tabla 'vehicles' - {len(vehicles)} vehículos registrados")
    except Exception as e:
        print(f"❌ Error verificando tabla 'vehicles': {e}")

    print()
    print("=" * 70)
    print("✓ INICIALIZACIÓN COMPLETADA")
    print("=" * 70)
    print()
    print("Próximos pasos:")
    print("1. Ejecuta el servidor: python obd_server.py")
    print("2. Abre index.html en tu navegador")
    print("3. Añade tu primer vehículo desde la interfaz")
    print()
    print("📁 Base de datos creada en:", os.path.abspath(database.DATABASE_NAME))
    print()

if __name__ == "__main__":
    main()
