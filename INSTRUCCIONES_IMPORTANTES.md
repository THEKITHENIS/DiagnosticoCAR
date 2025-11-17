# ⚠️ INSTRUCCIONES IMPORTANTES - ARCHIVOS PENDIENTES

He modificado tu aplicación SENTINEL PRO para que funcione con múltiples vehículos y base de datos SQLite.

## ✅ ARCHIVOS COMPLETADOS (listos para usar)

1. **database.py** ✅ - Módulo completo de gestión SQLite
2. **init_database.py** ✅ - Script de inicialización
3. **obd_server.py** ✅ - Servidor modificado con todos los endpoints REST
4. **index.html** ✅ - HTML modificado con gestión de vehículos y modal
5. **README.md** ✅ - Instrucciones completas de instalación y uso

## ⚠️ ARCHIVOS QUE NECESITAS ACTUALIZAR MANUALMENTE

Debido al límite de espacio en esta conversación, necesitas actualizar estos 2 archivos:

### 1. **script.js** - NECESITA ACTUALIZACIÓN COMPLETA

Tu archivo actual `script.js` NO incluye las funciones de gestión de vehículos.

**NECESITAS AÑADIR** estas funcionalidades al principio del archivo (después de las variables globales):

```javascript
// === NUEVAS VARIABLES GLOBALES PARA MULTI-VEHÍCULO ===
let allVehicles = [];
let activeVehicleId = null;
let currentEditingVehicleId = null;

// === FUNCIONES DE GESTIÓN DE VEHÍCULOS ===

async function loadVehicles() {
    try {
        const response = await fetch(`${API_URL}/api/vehicles`);
        const result = await response.json();

        if (result.success) {
            allVehicles = result.vehicles;
            renderVehiclesList();
            updateQuickSelector();
        }
    } catch (error) {
        console.error('[VEHICLES] Error cargando vehículos:', error);
    }
}

async function loadActiveVehicle() {
    try {
        const response = await fetch(`${API_URL}/api/vehicles/active`);
        const result = await response.json();

        if (result.success && result.active_vehicle_id) {
            activeVehicleId = result.active_vehicle_id;
            displayActiveVehicleConfig(result.vehicle);
            localStorage.setItem('activeVehicleId', activeVehicleId);
        }
    } catch (error) {
        console.error('[VEHICLES] Error cargando vehículo activo:', error);
    }
}

function renderVehiclesList() {
    const vehiclesList = document.getElementById('vehiclesList');

    if (allVehicles.length === 0) {
        vehiclesList.innerHTML = `
            <div class="no-vehicles-message">
                <i class="fas fa-car-side" style="font-size: 3rem; color: #cbd5e1;"></i>
                <h3>No hay vehículos registrados</h3>
                <p>Añade tu primer vehículo para comenzar</p>
            </div>
        `;
        return;
    }

    vehiclesList.innerHTML = allVehicles.map(vehicle => `
        <div class="vehicle-card ${vehicle.id === activeVehicleId ? 'active' : ''}" data-vehicle-id="${vehicle.id}">
            ${vehicle.id === activeVehicleId ? '<div class="active-badge"><i class="fas fa-check-circle"></i> ACTIVO</div>' : ''}
            <div class="vehicle-card-header">
                <div class="vehicle-icon">
                    <i class="fas fa-car"></i>
                </div>
                <div class="vehicle-info">
                    <h3>${vehicle.brand} ${vehicle.model}</h3>
                    <p class="vehicle-year">${vehicle.year} | ${vehicle.fuel_type.charAt(0).toUpperCase() + vehicle.fuel_type.slice(1)}</p>
                </div>
            </div>
            <div class="vehicle-card-body">
                <div class="vehicle-stat">
                    <i class="fas fa-road"></i>
                    <span>${Number(vehicle.mileage).toLocaleString()} km</span>
                </div>
                ${vehicle.statistics && vehicle.statistics.health_score ? `
                <div class="vehicle-stat">
                    <i class="fas fa-heartbeat"></i>
                    <span>Salud: ${vehicle.statistics.health_score}/100</span>
                </div>
                ` : ''}
                ${vehicle.plate ? `
                <div class="vehicle-stat">
                    <i class="fas fa-id-card"></i>
                    <span>${vehicle.plate}</span>
                </div>
                ` : ''}
            </div>
            <div class="vehicle-card-actions">
                ${vehicle.id !== activeVehicleId ? `
                <button class="btn btn-primary btn-select" onclick="selectVehicle(${vehicle.id})">
                    <i class="fas fa-check"></i> Seleccionar
                </button>
                ` : ''}
                <button class="btn btn-secondary btn-edit" onclick="editVehicle(${vehicle.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn btn-danger btn-delete" onclick="deleteVehicle(${vehicle.id})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    `).join('');
}

async function selectVehicle(vehicleId) {
    try {
        const response = await fetch(`${API_URL}/api/vehicles/${vehicleId}/select`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            activeVehicleId = vehicleId;
            showConnectionNotification(`Vehículo seleccionado: ${result.vehicle.brand} ${result.vehicle.model}`, 'success');
            loadVehicles();
            loadActiveVehicle();
        }
    } catch (error) {
        alert('Error al seleccionar vehículo: ' + error.message);
    }
}

function displayActiveVehicleConfig(vehicle) {
    if (!vehicle) {
        document.getElementById('noActiveVehicleMessage').style.display = 'block';
        document.getElementById('activeVehicleConfig').style.display = 'none';
        return;
    }

    document.getElementById('noActiveVehicleMessage').style.display = 'none';
    document.getElementById('activeVehicleConfig').style.display = 'block';

    document.getElementById('vehicleBrand').value = vehicle.brand || '';
    document.getElementById('vehicleModel').value = vehicle.model || '';
    document.getElementById('vehicleYear').value = vehicle.year || '';
    document.getElementById('vehicleMileage').value = vehicle.mileage || '';
    document.getElementById('vehicleType').value = vehicle.fuel_type || 'gasolina';
}

// === MODAL DE VEHÍCULO ===

const vehicleModal = document.getElementById('vehicleModal');
const vehicleForm = document.getElementById('vehicleForm');
const addVehicleBtn = document.getElementById('addVehicleBtn');
const modalClose = document.querySelector('.modal-close');
const modalCancel = document.querySelector('.modal-cancel');

addVehicleBtn.addEventListener('click', () => {
    currentEditingVehicleId = null;
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-car"></i> Añadir Nuevo Vehículo';
    vehicleForm.reset();
    vehicleModal.style.display = 'block';
});

modalClose.addEventListener('click', () => {
    vehicleModal.style.display = 'none';
});

modalCancel.addEventListener('click', () => {
    vehicleModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === vehicleModal) {
        vehicleModal.style.display = 'none';
    }
});

vehicleForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const vehicleData = {
        brand: document.getElementById('modalVehicleBrand').value,
        model: document.getElementById('modalVehicleModel').value,
        year: parseInt(document.getElementById('modalVehicleYear').value),
        mileage: parseInt(document.getElementById('modalVehicleMileage').value),
        fuel_type: document.getElementById('modalVehicleType').value,
        vin: document.getElementById('modalVehicleVIN').value || null,
        plate: document.getElementById('modalVehiclePlate').value || null
    };

    try {
        let response;
        if (currentEditingVehicleId) {
            response = await fetch(`${API_URL}/api/vehicles/${currentEditingVehicleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vehicleData)
            });
        } else {
            response = await fetch(`${API_URL}/api/vehicles`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vehicleData)
            });
        }

        const result = await response.json();

        if (result.success) {
            showConnectionNotification(result.message, 'success');
            vehicleModal.style.display = 'none';
            loadVehicles();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error al guardar vehículo: ' + error.message);
    }
});

function editVehicle(vehicleId) {
    const vehicle = allVehicles.find(v => v.id === vehicleId);
    if (!vehicle) return;

    currentEditingVehicleId = vehicleId;
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-edit"></i> Editar Vehículo';

    document.getElementById('modalVehicleBrand').value = vehicle.brand;
    document.getElementById('modalVehicleModel').value = vehicle.model;
    document.getElementById('modalVehicleYear').value = vehicle.year;
    document.getElementById('modalVehicleMileage').value = vehicle.mileage;
    document.getElementById('modalVehicleType').value = vehicle.fuel_type;
    document.getElementById('modalVehicleVIN').value = vehicle.vin || '';
    document.getElementById('modalVehiclePlate').value = vehicle.plate || '';

    vehicleModal.style.display = 'block';
}

async function deleteVehicle(vehicleId) {
    const vehicle = allVehicles.find(v => v.id === vehicleId);
    if (!vehicle) return;

    if (!confirm(`¿Estás seguro de que deseas eliminar ${vehicle.brand} ${vehicle.model}?\n\nEsto eliminará TODOS los datos asociados (telemetría, mantenimiento, análisis).`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/vehicles/${vehicleId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showConnectionNotification('Vehículo eliminado correctamente', 'success');
            loadVehicles();

            if (vehicleId === activeVehicleId) {
                activeVehicleId = null;
                loadActiveVehicle();
            }
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error al eliminar vehículo: ' + error.message);
    }
}

function updateQuickSelector() {
    const quickSelector = document.getElementById('quickVehicleSelector');
    const headerSelector = document.getElementById('headerVehicleSelector');

    if (allVehicles.length === 0) {
        headerSelector.style.display = 'none';
        return;
    }

    headerSelector.style.display = 'flex';

    quickSelector.innerHTML = '<option value="">Seleccionar vehículo...</option>';

    allVehicles.forEach(vehicle => {
        const option = document.createElement('option');
        option.value = vehicle.id;
        option.textContent = `${vehicle.brand} ${vehicle.model} (${vehicle.year})`;
        if (vehicle.id === activeVehicleId) {
            option.selected = true;
        }
        quickSelector.appendChild(option);
    });
}

document.getElementById('quickVehicleSelector').addEventListener('change', async (e) => {
    const vehicleId = parseInt(e.target.value);
    if (vehicleId) {
        await selectVehicle(vehicleId);
    }
});

// === BACKUP DE BASE DE DATOS ===

document.getElementById('backupDatabaseBtn').addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_URL}/api/backup/database`);

        if (!response.ok) throw new Error('Error al crear backup');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sentinel_pro_backup_${new Date().toISOString().split('T')[0]}.db`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showConnectionNotification('Backup descargado correctamente', 'success');
    } catch (error) {
        alert('Error al descargar backup: ' + error.message);
    }
});

// === INICIALIZACIÓN AL CARGAR LA PÁGINA ===

// AL FINAL DEL DOMContentLoaded, AÑADE:
loadVehicles();
loadActiveVehicle();
```

**IMPORTANTE**: Estas funciones deben añadirse a tu script.js existente. Mantén TODAS las funciones que ya tienes y añade estas nuevas.

---

### 2. **style.css** - NECESITA AÑADIR ESTILOS NUEVOS

Añade estos estilos al FINAL de tu archivo `style.css`:

```css
/* ========================================================================
   ESTILOS PARA GESTIÓN DE VEHÍCULOS Y MODAL
   ======================================================================== */

/* Header con selector de vehículo */
.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.header-title {
    flex: 1;
}

.header-vehicle-selector {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.1);
    padding: 10px 15px;
    border-radius: 8px;
}

.vehicle-dropdown {
    background: white;
    color: #1e293b;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
    min-width: 250px;
}

/* Sección de gestión de vehículos */
.vehicle-management-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-left: 4px solid #3b82f6;
}

.section-description {
    color: #64748b;
    margin-bottom: 1.5rem;
}

.vehicle-management-actions {
    margin: 1.5rem 0;
}

/* Grid de vehículos */
.vehicles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 1.5rem;
}

.no-vehicles-message {
    grid-column: 1 / -1;
    text-align: center;
    padding: 3rem;
    color: #94a3b8;
}

/* Tarjetas de vehículo */
.vehicle-card {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.vehicle-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
}

.vehicle-card.active {
    border-color: #10b981;
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.active-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #10b981;
    color: white;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 5px;
}

.vehicle-card-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
}

.vehicle-icon {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.5rem;
}

.vehicle-card.active .vehicle-icon {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.vehicle-info h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #1e293b;
}

.vehicle-year {
    margin: 5px 0 0;
    color: #64748b;
    font-size: 0.85rem;
}

.vehicle-card-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 15px;
}

.vehicle-stat {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #475569;
    font-size: 0.9rem;
}

.vehicle-stat i {
    color: #3b82f6;
    width: 20px;
}

.vehicle-card-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.vehicle-card-actions .btn {
    flex: 1;
    min-width: 0;
    padding: 8px 12px;
    font-size: 0.85rem;
}

.btn-danger {
    background-color: #ef4444;
}

.btn-danger:hover {
    background-color: #dc2626;
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    z-index: 10000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    overflow-y: auto;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.modal-content {
    background-color: white;
    margin: 5% auto;
    border-radius: 12px;
    max-width: 700px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        transform: translateY(-50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.modal-header {
    padding: 20px 25px;
    border-bottom: 2px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h2 {
    margin: 0;
    padding: 0;
    border: none;
}

.modal-close {
    color: #94a3b8;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    transition: color 0.2s;
}

.modal-close:hover {
    color: #ef4444;
}

.modal-content form {
    padding: 25px;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 25px;
    padding-top: 20px;
    border-top: 1px solid #e2e8f0;
}

.btn-secondary {
    background-color: #64748b;
}

.btn-secondary:hover {
    background-color: #475569;
}

/* Mensajes informativos */
.info-message {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 15px;
    border-radius: 8px;
    color: #1e40af;
    display: flex;
    align-items: center;
    gap: 10px;
}

.info-note {
    background: #f8fafc;
    border-left: 3px solid #94a3b8;
    padding: 12px;
    border-radius: 6px;
    color: #64748b;
    font-size: 0.9rem;
    margin-top: 15px;
}

/* Responsive */
@media (max-width: 768px) {
    .header-content {
        flex-direction: column;
        align-items: stretch;
    }

    .header-vehicle-selector {
        width: 100%;
    }

    .vehicle-dropdown {
        width: 100%;
    }

    .vehicles-grid {
        grid-template-columns: 1fr;
    }

    .vehicle-card-actions {
        flex-direction: column;
    }

    .vehicle-card-actions .btn {
        width: 100%;
    }

    .modal-content {
        margin: 10% 10px;
        max-width: none;
    }
}
```

---

## 🚀 PASOS SIGUIENTES

1. **Abre tu archivo `script.js` existente**
2. **Copia y pega** TODO el código de la sección "script.js - NECESITA ACTUALIZACIÓN"
3. **Abre tu archivo `style.css` existente**
4. **Copia y pega** TODO el código de estilos al FINAL del archivo
5. **Ejecuta** `python init_database.py` para crear la base de datos
6. **Ejecuta** `python obd_server.py` para iniciar el servidor
7. **Abre** `index.html` en tu navegador

---

## ✅ CHECKLIST FINAL

- [ ] database.py creado ✅
- [ ] init_database.py creado ✅
- [ ] obd_server.py modificado ✅
- [ ] index.html modificado ✅
- [ ] README.md creado ✅
- [ ] script.js actualizado con funciones de vehículos ⚠️ (HAZLO MANUALMENTE)
- [ ] style.css actualizado con estilos nuevos ⚠️ (HAZLO MANUALMENTE)
- [ ] Base de datos inicializada (ejecutar init_database.py)
- [ ] Servidor funcionando (ejecutar obd_server.py)
- [ ] Primer vehículo añadido desde la interfaz

---

## ❓ ¿NECESITAS AYUDA?

Si tienes problemas:

1. Lee el README.md para instrucciones detalladas
2. Verifica que todos los archivos estén en su lugar
3. Revisa la consola del servidor para errores
4. Abre la consola del navegador (F12) para ver errores JavaScript

---

**¡Tu aplicación SENTINEL PRO v10.0 Multi-Vehículo está casi lista!**

Solo faltan 2 pasos manuales simples: actualizar script.js y style.css con el código proporcionado arriba.
