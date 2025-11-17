// =============================================================================
// SENTINEL PRO v10.0 - GESTIÓN DE VEHÍCULOS (vehiculos.js)
// Copia y pega TODO este archivo como vehiculos.js
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // === CONFIGURACIÓN ===
    const API_URL = 'http://localhost:5000';

    // Variables globales
    let allVehicles = [];
    let filteredVehicles = [];
    let vehicleToDelete = null;

    // === FUNCIONES DE CARGA Y RENDERIZADO ===

    async function loadVehicles() {
        try {
            const response = await fetch(`${API_URL}/get_vehicles`);
            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error cargando vehículos');

            allVehicles = result.vehicles || [];
            applyFilters();
            updateFleetStats();

        } catch (error) {
            console.error('[VEHICLES] Error:', error);
            showNotification('Error cargando vehículos', 'error');
        }
    }

    function applyFilters() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const fuelFilter = document.getElementById('fuelTypeFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const sortBy = document.getElementById('sortBy').value;

        // Filtrar
        filteredVehicles = allVehicles.filter(vehicle => {
            // Búsqueda por texto
            const matchesSearch =
                vehicle.brand.toLowerCase().includes(searchTerm) ||
                vehicle.model.toLowerCase().includes(searchTerm) ||
                (vehicle.license_plate && vehicle.license_plate.toLowerCase().includes(searchTerm));

            // Filtro por combustible
            const matchesFuel = fuelFilter === 'all' || vehicle.fuel_type === fuelFilter;

            // Filtro por estado
            const matchesStatus = statusFilter === 'all' ||
                (statusFilter === 'active' && vehicle.is_active) ||
                (statusFilter === 'inactive' && !vehicle.is_active);

            return matchesSearch && matchesFuel && matchesStatus;
        });

        // Ordenar
        switch(sortBy) {
            case 'date_desc':
                filteredVehicles.sort((a, b) => b.id - a.id);
                break;
            case 'date_asc':
                filteredVehicles.sort((a, b) => a.id - b.id);
                break;
            case 'mileage_asc':
                filteredVehicles.sort((a, b) => a.mileage - b.mileage);
                break;
            case 'mileage_desc':
                filteredVehicles.sort((a, b) => b.mileage - a.mileage);
                break;
            case 'brand':
                filteredVehicles.sort((a, b) => a.brand.localeCompare(b.brand));
                break;
        }

        renderVehicles();
    }

    function renderVehicles() {
        const grid = document.getElementById('vehiclesGrid');
        const noResults = document.getElementById('noVehiclesFound');

        if (filteredVehicles.length === 0) {
            grid.style.display = 'none';
            noResults.style.display = 'flex';
            return;
        }

        grid.style.display = 'grid';
        noResults.style.display = 'none';

        grid.innerHTML = filteredVehicles.map(vehicle => {
            const isActive = vehicle.is_active ? 'active' : '';
            const fuelClass = vehicle.fuel_type ? vehicle.fuel_type.toLowerCase() : 'gasolina';
            const healthScore = 95; // Simulado - debería venir de la BD
            const healthClass = getHealthClass(healthScore);
            const lastConnection = 'Hace 2 horas'; // Simulado - debería venir de la BD

            return `
                <div class="vehicle-card-detailed ${isActive}">
                    <div class="vehicle-card-header-detailed">
                        <div class="vehicle-status-badge ${isActive ? 'badge-active' : 'badge-inactive'}">
                            ${isActive ? '✓ ACTIVO' : 'INACTIVO'}
                        </div>
                        <div class="vehicle-health-indicator ${healthClass}">
                            <i class="fas fa-heart"></i>
                            ${healthScore}
                        </div>
                        <div class="vehicle-actions-mini">
                            <button class="btn-mini btn-edit" onclick="editVehicle(${vehicle.id})" title="Editar">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-mini btn-delete" onclick="openDeleteModal(${vehicle.id}, '${vehicle.brand} ${vehicle.model}')" title="Eliminar">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>

                    <div class="vehicle-card-body-detailed">
                        <div class="vehicle-icon-large">
                            <i class="fas fa-car"></i>
                        </div>
                        <div class="vehicle-main-info">
                            <h3 class="vehicle-name">${vehicle.brand} ${vehicle.model}</h3>
                            <p class="vehicle-year"><i class="fas fa-calendar"></i> ${vehicle.year}</p>
                        </div>
                    </div>

                    <div class="vehicle-specs">
                        <div class="spec-item">
                            <i class="fas fa-road"></i>
                            <span>${vehicle.mileage.toLocaleString()} km</span>
                        </div>
                        <div class="spec-item">
                            <i class="fas fa-gas-pump"></i>
                            <span class="fuel-badge ${fuelClass}">${vehicle.fuel_type}</span>
                        </div>
                        ${vehicle.license_plate ? `
                        <div class="spec-item">
                            <i class="fas fa-id-card"></i>
                            <span>${vehicle.license_plate}</span>
                        </div>
                        ` : ''}
                        <div class="spec-item">
                            <i class="fas fa-signal"></i>
                            <span>${lastConnection}</span>
                        </div>
                    </div>

                    <div class="vehicle-card-footer-detailed">
                        ${!vehicle.is_active ? `
                        <button class="btn btn-small btn-success btn-full" onclick="setActiveVehicle(${vehicle.id})">
                            <i class="fas fa-check"></i> Seleccionar
                        </button>
                        ` : `
                        <button class="btn btn-small btn-primary btn-full" onclick="goToDashboard()">
                            <i class="fas fa-tachometer-alt"></i> Ver Dashboard
                        </button>
                        `}
                        <button class="btn btn-small btn-secondary btn-full" onclick="viewDetails(${vehicle.id})">
                            <i class="fas fa-info-circle"></i> Ver Detalles
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function updateFleetStats() {
        document.getElementById('totalVehicles').textContent = allVehicles.length;

        const connectedToday = allVehicles.filter(v => Math.random() > 0.3).length; // Simulado
        document.getElementById('connectedToday').textContent = connectedToday;

        const withWarnings = allVehicles.filter(v => Math.random() > 0.8).length; // Simulado
        document.getElementById('withWarnings').textContent = withWarnings;

        const avgHealth = allVehicles.length > 0 ? 95 : '--'; // Simulado
        document.getElementById('avgHealth').textContent = avgHealth + (allVehicles.length > 0 ? '/100' : '');
    }

    function getHealthClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'warning';
        return 'critical';
    }

    // === FUNCIONES DEL MODAL DE VEHÍCULO ===

    function openModal() {
        console.log('Abriendo modal');
        const modal = document.getElementById('vehicleModal');

        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';

            // Limpiar formulario
            document.getElementById('vehicleForm').reset();
            document.getElementById('vehicleId').value = '';
            document.getElementById('modalTitleText').textContent = 'Añadir Nuevo Vehículo';
        } else {
            console.error('Modal no encontrado');
        }
    }

    function closeModal() {
        const modal = document.getElementById('vehicleModal');

        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    async function saveVehicle(event) {
        event.preventDefault();

        const vehicleData = {
            id: document.getElementById('vehicleId').value || null,
            brand: document.getElementById('modalVehicleBrand').value,
            model: document.getElementById('modalVehicleModel').value,
            year: parseInt(document.getElementById('modalVehicleYear').value),
            mileage: parseInt(document.getElementById('modalVehicleMileage').value),
            fuel_type: document.getElementById('modalVehicleType').value,
            vin: document.getElementById('modalVehicleVIN').value || null,
            license_plate: document.getElementById('modalVehiclePlate').value.toUpperCase() || null
        };

        try {
            const response = await fetch(`${API_URL}/save_vehicle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vehicleData)
            });

            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error guardando vehículo');

            showNotification(vehicleData.id ? 'Vehículo actualizado correctamente' : 'Vehículo añadido correctamente', 'success');
            closeModal();
            loadVehicles();

        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        }
    }

    // === FUNCIONES DEL MODAL DE ELIMINACIÓN ===

    function openDeleteModal(vehicleId, vehicleName) {
        vehicleToDelete = { id: vehicleId, name: vehicleName };

        document.getElementById('vehicleToDeleteName').textContent = vehicleName;
        document.getElementById('deleteHint').textContent = `Escribe: "${vehicleName}"`;
        document.getElementById('deleteConfirmInput').value = '';
        document.getElementById('confirmDeleteBtn').disabled = true;

        const deleteModal = document.getElementById('deleteModal');
        deleteModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeDeleteModal() {
        const deleteModal = document.getElementById('deleteModal');
        deleteModal.classList.remove('active');
        document.body.style.overflow = '';
        vehicleToDelete = null;
    }

    function validateDeleteInput() {
        const input = document.getElementById('deleteConfirmInput').value;
        const confirmBtn = document.getElementById('confirmDeleteBtn');

        if (vehicleToDelete && input === vehicleToDelete.name) {
            confirmBtn.disabled = false;
        } else {
            confirmBtn.disabled = true;
        }
    }

    async function confirmDelete() {
        if (!vehicleToDelete) return;

        try {
            const response = await fetch(`${API_URL}/delete_vehicle/${vehicleToDelete.id}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error eliminando vehículo');

            showNotification('Vehículo eliminado correctamente', 'success');
            closeDeleteModal();
            loadVehicles();

        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        }
    }

    // === FUNCIONES DEL MODAL DE DETALLES ===

    async function viewDetails(vehicleId) {
        try {
            const response = await fetch(`${API_URL}/get_vehicle/${vehicleId}`);
            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error');

            const vehicle = result.vehicle;

            document.getElementById('detailsModalTitle').textContent = `${vehicle.brand} ${vehicle.model} (${vehicle.year})`;

            const detailsBody = document.getElementById('detailsModalBody');
            detailsBody.innerHTML = `
                <div class="details-grid">
                    <div class="details-section">
                        <h3><i class="fas fa-info-circle"></i> Información General</h3>
                        <div class="details-list">
                            <div class="detail-row">
                                <span class="detail-label">Marca:</span>
                                <span class="detail-value">${vehicle.brand}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Modelo:</span>
                                <span class="detail-value">${vehicle.model}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Año:</span>
                                <span class="detail-value">${vehicle.year}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Kilometraje:</span>
                                <span class="detail-value">${vehicle.mileage.toLocaleString()} km</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Combustible:</span>
                                <span class="detail-value">${vehicle.fuel_type}</span>
                            </div>
                            ${vehicle.license_plate ? `
                            <div class="detail-row">
                                <span class="detail-label">Matrícula:</span>
                                <span class="detail-value">${vehicle.license_plate}</span>
                            </div>
                            ` : ''}
                            ${vehicle.vin ? `
                            <div class="detail-row">
                                <span class="detail-label">VIN:</span>
                                <span class="detail-value">${vehicle.vin}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>

                    <div class="details-section">
                        <h3><i class="fas fa-chart-line"></i> Salud Histórica (Últimos 30 días)</h3>
                        <div class="health-chart-placeholder">
                            <i class="fas fa-chart-area" style="font-size: 3rem; color: #cbd5e1;"></i>
                            <p style="color: #94a3b8; margin-top: 1rem;">Gráfico de salud no disponible</p>
                            <p style="color: #cbd5e1; font-size: 0.9rem;">Conecta el vehículo al sistema OBD-II para registrar datos</p>
                        </div>
                    </div>

                    <div class="details-section">
                        <h3><i class="fas fa-wrench"></i> Últimos Mantenimientos</h3>
                        <div class="maintenance-list-details">
                            <div class="maintenance-item-details">
                                <i class="fas fa-oil-can"></i>
                                <div>
                                    <strong>Cambio de aceite</strong>
                                    <span>15/01/2025 - 94,500 km</span>
                                </div>
                            </div>
                            <div class="maintenance-item-details">
                                <i class="fas fa-filter"></i>
                                <div>
                                    <strong>Cambio de filtro de aire</strong>
                                    <span>10/12/2024 - 92,000 km</span>
                                </div>
                            </div>
                            <div class="maintenance-item-details">
                                <i class="fas fa-tire"></i>
                                <div>
                                    <strong>Rotación de neumáticos</strong>
                                    <span>05/11/2024 - 90,000 km</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="details-section">
                        <h3><i class="fas fa-route"></i> Últimos Viajes</h3>
                        <div class="trips-list-details">
                            <div class="trip-item-details">
                                <i class="fas fa-calendar-day"></i>
                                <div>
                                    <strong>17/01/2025</strong>
                                    <span>45 km - 1h 20min - Promedio: 85 km/h</span>
                                </div>
                            </div>
                            <div class="trip-item-details">
                                <i class="fas fa-calendar-day"></i>
                                <div>
                                    <strong>16/01/2025</strong>
                                    <span>12 km - 25min - Promedio: 28 km/h</span>
                                </div>
                            </div>
                            <div class="trip-item-details">
                                <i class="fas fa-calendar-day"></i>
                                <div>
                                    <strong>15/01/2025</strong>
                                    <span>32 km - 40min - Promedio: 48 km/h</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="details-footer">
                    <button class="btn btn-primary" onclick="closeDetailsModal()">
                        <i class="fas fa-check"></i> Cerrar
                    </button>
                    <button class="btn btn-secondary" onclick="editVehicle(${vehicle.id}); closeDetailsModal();">
                        <i class="fas fa-edit"></i> Editar Vehículo
                    </button>
                </div>
            `;

            const detailsModal = document.getElementById('detailsModal');
            detailsModal.classList.add('active');
            document.body.style.overflow = 'hidden';

        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        }
    }

    function closeDetailsModal() {
        const detailsModal = document.getElementById('detailsModal');
        detailsModal.classList.remove('active');
        document.body.style.overflow = '';
    }

    // === FUNCIONES GLOBALES ===

    window.editVehicle = async function(vehicleId) {
        try {
            const response = await fetch(`${API_URL}/get_vehicle/${vehicleId}`);
            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error');

            const vehicle = result.vehicle;

            document.getElementById('vehicleId').value = vehicle.id;
            document.getElementById('modalVehicleBrand').value = vehicle.brand;
            document.getElementById('modalVehicleModel').value = vehicle.model;
            document.getElementById('modalVehicleYear').value = vehicle.year;
            document.getElementById('modalVehicleMileage').value = vehicle.mileage;
            document.getElementById('modalVehicleType').value = vehicle.fuel_type;
            document.getElementById('modalVehicleVIN').value = vehicle.vin || '';
            document.getElementById('modalVehiclePlate').value = vehicle.license_plate || '';
            document.getElementById('modalTitleText').textContent = 'Editar Vehículo';

            openModal();

        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        }
    };

    window.setActiveVehicle = async function(vehicleId) {
        try {
            const response = await fetch(`${API_URL}/set_active_vehicle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_id: vehicleId })
            });

            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error');

            showNotification('Vehículo seleccionado como activo', 'success');
            loadVehicles();

        } catch (error) {
            showNotification(`Error: ${error.message}`, 'error');
        }
    };

    window.openDeleteModal = openDeleteModal;
    window.viewDetails = viewDetails;
    window.closeDetailsModal = closeDetailsModal;

    window.goToDashboard = function() {
        window.location.href = 'index.html';
    };

    // === EXPORTAR A CSV ===

    function exportToCSV() {
        if (allVehicles.length === 0) {
            showNotification('No hay vehículos para exportar', 'warning');
            return;
        }

        let csv = 'Marca,Modelo,Año,Kilometraje,Combustible,Matrícula,VIN,Estado\n';

        allVehicles.forEach(vehicle => {
            csv += `${vehicle.brand},${vehicle.model},${vehicle.year},${vehicle.mileage},${vehicle.fuel_type},`;
            csv += `${vehicle.license_plate || ''},${vehicle.vin || ''},${vehicle.is_active ? 'Activo' : 'Inactivo'}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sentinel_vehiculos_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showNotification('Archivo CSV descargado', 'success');
    }

    // === NOTIFICACIONES ===

    function showNotification(message, type = 'info') {
        const existingNotification = document.querySelector('.connection-notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `connection-notification ${type === 'error' ? 'warning' : type}`;

        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle';

        notification.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // === EVENT LISTENERS ===

    document.getElementById('addVehicleToolbarBtn').addEventListener('click', openModal);
    document.querySelector('.modal-close').addEventListener('click', closeModal);

    const cancelButtons = document.querySelectorAll('.modal-cancel');
    cancelButtons.forEach(btn => {
        btn.addEventListener('click', closeModal);
    });

    document.getElementById('vehicleModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
            closeDeleteModal();
            closeDetailsModal();
        }
    });

    document.getElementById('vehicleForm').addEventListener('submit', saveVehicle);

    // Event listeners del modal de eliminación
    document.querySelector('.modal-close-delete').addEventListener('click', closeDeleteModal);

    const cancelDeleteButtons = document.querySelectorAll('.modal-cancel-delete');
    cancelDeleteButtons.forEach(btn => {
        btn.addEventListener('click', closeDeleteModal);
    });

    document.getElementById('deleteModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeDeleteModal();
        }
    });

    document.getElementById('deleteConfirmInput').addEventListener('input', validateDeleteInput);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

    // Event listeners del modal de detalles
    document.querySelector('.modal-close-details').addEventListener('click', closeDetailsModal);

    document.getElementById('detailsModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeDetailsModal();
        }
    });

    // Event listeners de filtros y búsqueda
    document.getElementById('searchInput').addEventListener('input', applyFilters);
    document.getElementById('fuelTypeFilter').addEventListener('change', applyFilters);
    document.getElementById('statusFilter').addEventListener('change', applyFilters);
    document.getElementById('sortBy').addEventListener('change', applyFilters);
    document.getElementById('exportVehiclesBtn').addEventListener('click', exportToCSV);

    // === INICIALIZACIÓN ===

    console.log('[VEHICLES] Página de gestión de vehículos iniciada');
    loadVehicles();
});
