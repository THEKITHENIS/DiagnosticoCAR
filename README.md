# SENTINEL PRO v10.0 - Sistema Multi-Vehículo

## 📋 Descripción

**SENTINEL PRO** es un sistema inteligente de mantenimiento predictivo vehicular que utiliza:
- **Monitoreo OBD-II** en tiempo real
- **Base de datos SQLite** para persistencia multi-vehículo
- **Inteligencia Artificial** (Google Gemini) para análisis predictivo
- **Gestión completa** de múltiples vehículos

---

## ⚡ INSTALACIÓN RÁPIDA

### 1️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Inicializar Base de Datos

```bash
python init_database.py
```

### 3️⃣ (OPCIONAL) Migrar Datos Históricos

Si tienes archivos `health_history.json` o `historial_viajes.json`, migra los datos:

```bash
python migrate_json_to_db.py
```

**✅ Los archivos originales se copiarán a `backup/FECHA_HORA/` y NO serán eliminados.**

### 4️⃣ Configurar Conexión OBD-II y API

Edita el archivo `obd_server.py` y configura:

```python
# Líneas 26-28
OBD_PORT = "COM6"  # Cambia esto a tu puerto OBD-II (ej: COM3, /dev/ttyUSB0)
GEMINI_API_KEY = "TU_API_KEY_AQUI"  # Tu API key de Google Gemini
```

**Obtener API Key de Google Gemini:**
1. Ve a https://makersuite.google.com/app/apikey
2. Crea un nuevo proyecto
3. Genera una API Key
4. Cópiala en `GEMINI_API_KEY`

### 5️⃣ Iniciar Servidor

```bash
python obd_server.py
```

### 6️⃣ Abrir Aplicación

Abre tu navegador en:
```
http://localhost:5000
```

O simplemente abre el archivo `index.html` directamente.

---

## 🚗 PRIMER USO

### Añadir tu Primer Vehículo

1. Haz clic en **"Añadir Nuevo Vehículo"** en la sección de Gestión de Vehículos
2. Rellena los datos:
   - **Marca** (ej: Seat)
   - **Modelo y Motor** (ej: León 2.0 TDI)
   - **Año** (ej: 2018)
   - **Kilómetros** (ej: 95000)
   - **Tipo de Combustible** (Gasolina, Diésel, Híbrido, Eléctrico)
   - *Opcional:* VIN, Matrícula

3. Haz clic en **"Guardar Vehículo"**
4. Haz clic en **"Seleccionar"** para activarlo como vehículo activo
5. Conecta tu adaptador OBD-II al vehículo
6. Enciende el motor
7. ¡SENTINEL PRO comenzará a monitorear automáticamente!

---

## ✨ CARACTERÍSTICAS PRINCIPALES

### ✅ Gestión Multi-Vehículo
- Añadir, editar y eliminar vehículos ilimitados
- Selector rápido de vehículo activo
- Historial completo por vehículo
- Estadísticas individuales

### ✅ Monitoreo OBD-II en Tiempo Real
- **Datos críticos cada 3 segundos:**
  - RPM del motor
  - Velocidad (km/h)
  - Posición del acelerador (%)
  - Carga del motor (%)
  - Flujo de aire MAF (g/s)
  - Distancia recorrida (km)

- **Datos térmicos cada 60 segundos:**
  - Temperatura del refrigerante (°C)
  - Temperatura de admisión (°C)

### ✅ Análisis Predictivo con IA
- Scoring de salud del vehículo (0-100)
- Predicción de fallos en 6-12 meses
- Detección de patrones de desgaste
- Recomendaciones de mantenimiento prioritario
- Estimación de costes preventivos vs correctivos

### ✅ Inteligencia Artificial Avanzada
- **Averías Comunes**: Base de conocimiento específica por modelo
- **Tasación Inteligente**: Valoración de mercado ajustada por uso y mantenimiento
- **Análisis de Conducción**: Detección de conducción agresiva

### ✅ Historial y Datos Persistentes
- Base de datos SQLite profesional
- Historial completo de telemetría
- Registro de mantenimiento por vehículo
- Análisis de salud histórico
- Backup automático de datos

### ✅ Gestión de Archivos CSV
- Importar datos históricos de viajes
- Exportar datos para análisis externo
- Descarga de informes en PDF

### ✅ Modal Profesional y Responsive
- Ventana flotante centrada con overlay oscuro
- Animaciones suaves
- Cierre con ESC, clic fuera o botón X
- Diseño adaptable a móvil y escritorio

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
DiagnosticoCAR/
├── obd_server.py              # Servidor backend Flask
├── database.py                # Módulo de base de datos SQLite
├── init_database.py           # Inicializador de BD
├── migrate_json_to_db.py      # Migrador de datos con backup
├── index.html                 # Frontend principal
├── script.js                  # Lógica JavaScript
├── style.css                  # Estilos CSS
├── requirements.txt           # Dependencias Python
├── sentinel_pro.db            # Base de datos SQLite (se crea automáticamente)
├── backup/                    # Backups automáticos
│   └── 2025-11-17_15-30/
│       ├── health_history.json
│       ├── historial_viajes.json
│       └── migration_report.txt
└── csv_data/                  # Datos CSV
    └── obd_readings.csv
```

---

## 🔧 CONFIGURACIÓN AVANZADA

### Cambiar Puerto del Servidor

En `obd_server.py` (línea 1222):
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

### Cambiar Puerto OBD-II

Los puertos comunes son:
- **Windows**: `COM3`, `COM4`, `COM5`, `COM6`
- **Linux**: `/dev/ttyUSB0`, `/dev/rfcomm0`
- **macOS**: `/dev/tty.usbserial`

### Intervalo de Lectura OBD-II

En `script.js` (línea 9):
```javascript
const POLL_INTERVAL = 3000; // Milisegundos (3000 = 3 segundos)
```

---

## 📊 BASE DE DATOS

### Tablas Principales

| Tabla | Descripción |
|-------|-------------|
| `vehicles` | Información de vehículos |
| `telemetry_data` | Datos OBD-II en tiempo real |
| `maintenance_records` | Historial de mantenimiento |
| `ai_analysis` | Análisis de IA y salud |

### Backup Manual de la Base de Datos

```bash
cp sentinel_pro.db sentinel_pro_backup.db
```

O desde la interfaz web:
1. Ve a la sección "Gestión de Archivos CSV"
2. Haz clic en **"Descargar Backup de Base de Datos"**

---

## 🛠️ SOLUCIÓN DE PROBLEMAS

### ❌ Error: "No se puede conectar a OBD-II"

**Soluciones:**
1. Verifica que el adaptador OBD-II esté conectado al puerto del vehículo
2. Verifica que el motor esté encendido
3. Comprueba que el puerto COM es correcto en `obd_server.py`
4. Asegúrate de que el adaptador es compatible (ELM327)

### ❌ Error: "API KEY no válida" (Gemini)

**Soluciones:**
1. Obtén una API Key en https://makersuite.google.com/app/apikey
2. Edita `obd_server.py` línea 27
3. Asegúrate de que la API Key tenga permisos activados

### ❌ El modal no se muestra correctamente

**Solución:**
- Asegúrate de que los archivos `style.css` y `script.js` estén correctamente vinculados
- Limpia la caché del navegador (Ctrl + F5)
- Verifica que no haya errores en la consola del navegador (F12)

### ❌ Los datos no se guardan

**Soluciones:**
1. Verifica que la base de datos se haya inicializado: `python init_database.py`
2. Comprueba los permisos de escritura en la carpeta del proyecto
3. Revisa la consola del servidor para ver errores

### ❌ Error en la migración de datos

**Solución:**
- Los archivos JSON deben estar en la raíz del proyecto
- Formato JSON válido (usa https://jsonlint.com/ para validar)
- Si falla, revisa `backup/FECHA_HORA/migration_report.txt`

---

## 📱 COMPATIBILIDAD

### Navegadores Soportados
- ✅ Google Chrome / Chromium (Recomendado)
- ✅ Mozilla Firefox
- ✅ Microsoft Edge
- ✅ Safari
- ⚠️ Internet Explorer (No soportado)

### Sistemas Operativos
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, Fedora)
- ✅ macOS

### Adaptadores OBD-II Compatibles
- ✅ ELM327 v1.5 (Bluetooth, USB, WiFi)
- ✅ OBDLink SX/MX/MX+
- ✅ BAFX Products 34t5
- ⚠️ Adaptadores chinos baratos (compatibilidad variable)

---

## 📝 NOTAS IMPORTANTES

### 🔒 Privacidad y Seguridad
- ✅ **Todos los datos se almacenan localmente** en tu ordenador
- ✅ No se envían datos a servidores externos (excepto Google Gemini para análisis IA)
- ✅ La base de datos NO está cifrada por defecto
- ⚠️ Haz backups regulares de `sentinel_pro.db`

### ⚡ Rendimiento
- El sistema está optimizado para lecturas cada 3 segundos
- La base de datos puede crecer significativamente con el tiempo
- Recomendado: Limpiar datos antiguos cada 6-12 meses

### 🚗 Compatibilidad Vehicular
- Funciona con **todos los vehículos OBD-II** (fabricados después de 2001)
- Algunos parámetros pueden no estar disponibles en vehículos antiguos
- Vehículos eléctricos tienen PIDs diferentes

---

## 🆘 SOPORTE Y CONTRIBUCIONES

### Reportar Errores
Si encuentras un error:
1. Abre un **Issue** en GitHub
2. Incluye:
   - Descripción del error
   - Pasos para reproducirlo
   - Captura de pantalla (si aplica)
   - Logs del servidor

### Contribuir
¡Las contribuciones son bienvenidas!
1. Haz un Fork del proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📜 LICENCIA

Este proyecto es de código abierto. Puedes usarlo, modificarlo y distribuirlo libremente.

---

## 🙏 CRÉDITOS

- **Python OBD**: https://github.com/brendan-w/python-OBD
- **Google Gemini AI**: https://ai.google.dev/
- **Flask Framework**: https://flask.palletsprojects.com/
- **Font Awesome Icons**: https://fontawesome.com/

---

## 🎯 ROADMAP FUTURO

- [ ] App móvil nativa (Android/iOS)
- [ ] Dashboard web remoto
- [ ] Integración con talleres mecánicos
- [ ] Alertas por email/SMS
- [ ] Sincronización en la nube
- [ ] Soporte para flotas empresariales
- [ ] Integración con OBD2 WiFi directo

---

**⭐ Si te gusta SENTINEL PRO, dale una estrella en GitHub ⭐**

**Versión:** 10.0 Multi-Vehículo
**Última actualización:** 17 de Noviembre de 2025
**Estado:** ✅ Estable y en producción
