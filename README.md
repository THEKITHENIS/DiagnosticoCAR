# SENTINEL PRO v10.0 - Sistema Multi-Vehículo con SQLite

Sistema profesional de mantenimiento predictivo vehicular con gestión de múltiples vehículos, base de datos SQLite persistente e inteligencia artificial.

## 🚀 Características Principales

### ✅ **MULTI-VEHÍCULO**
- Gestión ilimitada de vehículos
- Selector rápido en header
- Histórico independiente por vehículo
- Comparativas entre vehículos

### ✅ **BASE DE DATOS SQLite**
- Almacenamiento persistente de todos los datos
- Tablas: vehicles, telemetry_data, maintenance_records, ai_analysis
- Backup automático de base de datos
- Importación/exportación de datos

### ✅ **MONITOREO OBD-II EN TIEMPO REAL**
- Lectura cada 3 segundos: RPM, velocidad, acelerador, carga, MAF
- Lectura cada 60 segundos: temperaturas (refrigerante, admisión)
- Cálculo preciso de distancia recorrida
- Detección automática de viajes

### ✅ **ANÁLISIS PREDICTIVO CON IA (Google Gemini)**
- Predicción de fallos en 6-12 meses
- Scoring de salud del vehículo (0-100)
- Análisis de conducción y desgaste
- Averías comunes por modelo específico
- Tasación inteligente ajustada por mantenimiento

### ✅ **MANTENIMIENTO INTELIGENTE**
- Registro de intervenciones por vehículo
- Historial completo de mantenimiento
- Alertas preventivas automáticas
- Generación de informes PDF

### ✅ **GESTIÓN DE DATOS**
- Exportación CSV con todos los datos
- Generación de informes PDF profesionales
- Backup completo de base de datos
- Importación de CSV históricos

---

## 📦 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Adaptador OBD-II (ELM327 o similar)
- Google Gemini API Key (gratuita)

### Dependencias de Python

```bash
pip install flask
pip install flask-cors
pip install obd
pip install google-generativeai
pip install fpdf
pip install geocoder
```

### Configuración Inicial

1. **Clona o descarga** este repositorio:
   ```bash
   cd DiagnosticoCAR
   ```

2. **Edita `obd_server.py`** y configura:
   ```python
   OBD_PORT = "COM6"  # Cambia a tu puerto (COM3, /dev/ttyUSB0, etc.)
   GEMINI_API_KEY = "TU_API_KEY_AQUI"  # Obtén una gratis en ai.google.dev
   ```

3. **Inicializa la base de datos**:
   ```bash
   python init_database.py
   ```
   Esto creará el archivo `sentinel_pro.db` con todas las tablas necesarias.

4. **Inicia el servidor**:
   ```bash
   python obd_server.py
   ```
   Verás:
   ```
   ======================================================================
   SENTINEL PRO - MANTENIMIENTO PREDICTIVO v10.0 MULTI-VEHÍCULO
   ======================================================================
   [DATABASE] ✓ Base de datos inicializada
   [OBD] Conectando a COM6...
   [OBD] ✓ Conectado exitosamente
   ✓ Servidor activo en http://localhost:5000
   ```

5. **Abre `index.html`** en tu navegador (Chrome, Firefox, Edge)

---

## 🚗 Uso del Sistema

### 1. **Añadir tu Primer Vehículo**

1. Abre la aplicación en tu navegador
2. Ve a "Gestión de Vehículos"
3. Haz clic en "Añadir Nuevo Vehículo"
4. Completa el formulario:
   - **Marca** (ej: Seat)
   - **Modelo y Motor** (ej: León 2.0 TDI)
   - **Año** (ej: 2018)
   - **Kilómetros** (ej: 95000)
   - **Tipo de combustible** (Gasolina/Diesel/Híbrido/Eléctrico)
   - **VIN** (opcional: número de bastidor)
   - **Matrícula** (opcional)
5. Haz clic en "Guardar Vehículo"

### 2. **Seleccionar Vehículo Activo para Monitoreo**

1. En la sección "Gestión de Vehículos", haz clic en **"Seleccionar"** en el vehículo que deseas monitorear
2. Verás un indicador verde "ACTIVO" en la tarjeta del vehículo
3. El vehículo aparecerá en el selector del header
4. Todos los datos OBD-II se asociarán a este vehículo

### 3. **Monitoreo en Tiempo Real**

1. **Enciende tu vehículo** con el adaptador OBD-II conectado
2. La aplicación detectará automáticamente cuando el motor esté encendido (RPM > 400)
3. Verás datos actualizados cada 3 segundos en "Datos en Vivo"
4. El sistema guardará automáticamente:
   - Telemetría en la base de datos
   - Datos en archivo CSV
   - Análisis de salud cada 90 segundos

### 4. **Análisis Predictivo con IA**

1. **Conduce al menos 2 minutos** para recopilar datos suficientes
2. Haz clic en **"Análisis Predictivo con IA"**
3. El sistema generará:
   - Predicción de fallos en 6-12 meses
   - Mantenimiento prioritario
   - Estimación de costes
   - Scoring de componentes

### 5. **Registrar Mantenimiento**

1. Ve a "Registro de Mantenimiento"
2. Ingresa:
   - Tipo de intervención (ej: "Cambio de aceite")
   - Fecha de la intervención
3. Haz clic en "Registrar Intervención"
4. El historial se guardará en la base de datos asociado al vehículo activo

### 6. **Gestionar Múltiples Vehículos**

- **Cambiar de vehículo**: Usa el selector rápido en el header o selecciona desde "Gestión de Vehículos"
- **Editar vehículo**: Haz clic en "Editar" en la tarjeta del vehículo
- **Eliminar vehículo**: Haz clic en "Eliminar" (requiere confirmación)
- **Ver estadísticas**: Cada tarjeta muestra:
  - Salud general
  - Total de lecturas OBD-II
  - Última conexión
  - Registros de mantenimiento

---

## 📊 Estructura de la Base de Datos

### Tabla: **vehicles**
```sql
- id (PRIMARY KEY)
- brand (marca del vehículo)
- model (modelo y motor)
- year (año)
- mileage (kilómetros)
- fuel_type (gasolina, diesel, hibrido, electrico)
- vin (número de bastidor, opcional)
- plate (matrícula, opcional)
- created_at (fecha de creación)
- updated_at (fecha de última actualización)
```

### Tabla: **telemetry_data**
```sql
- id (PRIMARY KEY)
- vehicle_id (FOREIGN KEY a vehicles.id)
- timestamp (fecha y hora de la lectura)
- rpm, speed, throttle_position, engine_load
- coolant_temp, intake_temp, maf, distance
```

### Tabla: **maintenance_records**
```sql
- id (PRIMARY KEY)
- vehicle_id (FOREIGN KEY a vehicles.id)
- maintenance_type (tipo de intervención)
- maintenance_date (fecha de la intervención)
- notes (notas adicionales)
- created_at (fecha de registro)
```

### Tabla: **ai_analysis**
```sql
- id (PRIMARY KEY)
- vehicle_id (FOREIGN KEY a vehicles.id)
- analysis_date (fecha del análisis)
- health_score (puntuación 0-100)
- engine_health, thermal_health, efficiency_health
- predictions (JSON con predicciones)
- warnings (JSON con advertencias)
```

---

## 🔧 Endpoints REST API

### Vehículos
```
POST   /api/vehicles              - Crear nuevo vehículo
GET    /api/vehicles              - Obtener todos los vehículos
GET    /api/vehicles/<id>         - Obtener un vehículo específico
PUT    /api/vehicles/<id>         - Actualizar vehículo
DELETE /api/vehicles/<id>         - Eliminar vehículo
POST   /api/vehicles/<id>/select  - Seleccionar vehículo activo
GET    /api/vehicles/active       - Obtener vehículo activo
```

### Telemetría
```
GET    /api/telemetry/<vehicle_id>  - Obtener historial de telemetría
```

### Mantenimiento
```
POST   /api/maintenance               - Guardar registro de mantenimiento
GET    /api/maintenance/<vehicle_id>  - Obtener historial de mantenimiento
DELETE /api/maintenance/<record_id>   - Eliminar registro
```

### Análisis IA
```
POST   /api/analysis               - Guardar análisis de IA
GET    /api/analysis/<vehicle_id>  - Obtener historial de análisis
```

### Backup
```
GET    /api/backup/database        - Descargar backup de la base de datos
```

---

## 🛠️ Solución de Problemas

### Problema: "No se puede conectar al puerto OBD"

**Solución**:
1. Verifica que el adaptador OBD-II esté conectado al puerto del vehículo
2. Enciende el contacto del vehículo
3. En Windows: Abre el Administrador de Dispositivos → Puertos COM → Anota el puerto (ej: COM6)
4. En Linux: Usa `ls /dev/ttyUSB*` para ver puertos disponibles
5. Actualiza `OBD_PORT` en `obd_server.py`
6. Reinicia el servidor

### Problema: "Error de API de Gemini"

**Solución**:
1. Obtén una API Key gratuita en: https://ai.google.dev
2. Actualiza `GEMINI_API_KEY` en `obd_server.py`
3. Verifica que la key no tenga espacios ni comillas extra
4. Reinicia el servidor

### Problema: "No se guardan los datos en la base de datos"

**Solución**:
1. Verifica que existe el archivo `sentinel_pro.db` en la carpeta del proyecto
2. Ejecuta: `python init_database.py`
3. Verifica permisos de escritura en la carpeta
4. Revisa la consola del servidor para errores

### Problema: "El selector de vehículos está vacío"

**Solución**:
1. Verifica que el servidor esté en ejecución (`python obd_server.py`)
2. Abre la consola del navegador (F12) para ver errores
3. Verifica que la URL del API_URL en `script.js` sea `http://localhost:5000`
4. Añade al menos un vehículo desde "Gestión de Vehículos"

---

## 📝 Archivos del Proyecto

```
DiagnosticoCAR/
├── database.py              # Módulo de gestión de base de datos SQLite
├── init_database.py         # Script de inicialización de base de datos
├── obd_server.py            # Servidor Flask con endpoints REST
├── index.html               # Interfaz web principal
├── script.js                # Lógica JavaScript del frontend
├── style.css                # Estilos CSS
├── README.md                # Este archivo
├── sentinel_pro.db          # Base de datos SQLite (se crea al inicializar)
├── csv_data/                # Carpeta con archivos CSV generados
├── uploaded_csv/            # Carpeta con CSVs subidos por el usuario
└── health_history.json      # Historial de salud (legacy)
```

---

## 🔒 Seguridad y Privacidad

- **Todos los datos se almacenan localmente** en tu computadora
- No se envía información a servidores externos (excepto Google Gemini para análisis IA)
- La base de datos SQLite es un archivo local que puedes respaldar
- Recomendación: Haz backups regulares usando el botón "Descargar Backup"

---

## ⚙️ Configuración Avanzada

### Cambiar intervalo de lectura OBD-II

Edita en `obd_server.py`:
```python
POLL_INTERVAL = 3000  # Milisegundos (por defecto 3 segundos)
THERMAL_READING_INTERVAL = 60  # Segundos (por defecto 60 segundos)
```

### Cambiar modelo de IA de Gemini

Edita en `obd_server.py`:
```python
GEMINI_MODEL_NAME = "models/gemini-pro-latest"  # O "gemini-1.5-flash"
```

### Limpiar telemetría antigua

Ejecuta en Python:
```python
import database
database.delete_old_telemetry(days=30)  # Eliminar datos > 30 días
```

---

## 📈 Próximas Características (Roadmap)

- [ ] Comparativa entre vehículos (gráficas)
- [ ] Dashboard de flota con vista resumida
- [ ] Alertas por correo electrónico
- [ ] Exportación de informes personalizados
- [ ] Integración con calendarios para mantenimiento
- [ ] Modo offline completo
- [ ] App móvil (Android/iOS)

---

## 👨‍💻 Soporte

Si encuentras algún problema o tienes sugerencias:

1. Revisa la sección "Solución de Problemas"
2. Verifica que todas las dependencias estén instaladas
3. Consulta los mensajes de error en la consola del servidor
4. Abre un issue en el repositorio del proyecto

---

## 📄 Licencia

Este proyecto es de código abierto. Puedes usarlo, modificarlo y distribuirlo libremente.

---

## 🙏 Agradecimientos

- **Python-OBD** - Librería para comunicación OBD-II
- **Google Gemini** - Inteligencia artificial para análisis predictivo
- **Flask** - Framework web para el servidor
- **Font Awesome** - Iconos de la interfaz

---

**SENTINEL PRO v10.0** - Sistema profesional de mantenimiento predictivo vehicular

© 2025 - Desarrollado con ❤️ para la comunidad automotriz
