// Funciones de utilidad generales
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
};

const showNotification = (message, type = 'success') => {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded shadow-lg ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white z-50`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
};

// Gestión de menús y dropdowns
const initializeMenus = () => {
    if (window.Alpine) {
        Alpine.store('menuState', {
            dropdowns: {},
            closeAll() {
                this.dropdowns = {};
            }
        });

        // Cerrar menús cuando se hace clic fuera
        document.addEventListener('click', (e) => {
            if (!e.target.closest('[x-data]')) {
                Alpine.store('menuState').closeAll();
            }
        });

        // Cerrar menús con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                Alpine.store('menuState').closeAll();
            }
        });
    }
};

// Funciones para productos
const deleteProduct = async (productId) => {
    if (!confirm('¿Está seguro de que desea eliminar este producto?')) {
        return;
    }

    try {
        const response = await fetch(`/producto/${productId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            showNotification('Producto eliminado exitosamente');
            location.reload();
        } else {
            showNotification('Error al eliminar el producto', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al eliminar el producto', 'error');
    }
};

// Funciones para ventas
const calculateSubtotal = (cantidad, precioUnitario) => {
    return (parseFloat(cantidad) * parseFloat(precioUnitario)).toFixed(2);
};

const updateTotals = () => {
    let total = 0;
    document.querySelectorAll('.producto-item').forEach(item => {
        const cantidad = parseFloat(item.querySelector('.cantidad').value) || 0;
        const precioUnitario = parseFloat(item.querySelector('.precio-unitario').value) || 0;
        const subtotal = cantidad * precioUnitario;
        item.querySelector('.subtotal').value = subtotal.toFixed(2);
        total += subtotal;
    });
    
    const totalElement = document.getElementById('total');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2);
    }
};

// Validaciones
const validateStock = (cantidad, stockDisponible) => {
    return parseInt(cantidad) <= parseInt(stockDisponible);
};

const validateForm = (formData) => {
    const errors = [];

    if (!formData.cliente_id) {
        errors.push('Debe seleccionar un cliente');
    }

    if (!formData.items || formData.items.length === 0) {
        errors.push('Debe agregar al menos un producto');
    }

    formData.items?.forEach((item, index) => {
        if (!item.producto_id) {
            errors.push(`Debe seleccionar un producto en la línea ${index + 1}`);
        }
        if (!item.cantidad || item.cantidad <= 0) {
            errors.push(`La cantidad debe ser mayor a 0 en la línea ${index + 1}`);
        }
        if (!item.precio_unitario || item.precio_unitario <= 0) {
            errors.push(`El precio debe ser mayor a 0 en la línea ${index + 1}`);
        }
    });

    return errors;
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar menús
    initializeMenus();

    // Inicializar eventos para productos existentes en ventas
    document.querySelectorAll('.producto-item').forEach(item => {
        const productoSelect = item.querySelector('.producto-select');
        const cantidadInput = item.querySelector('.cantidad');
        
        if (productoSelect && cantidadInput) {
            productoSelect.addEventListener('change', () => {
                const option = productoSelect.options[productoSelect.selectedIndex];
                const precioUnitario = option.dataset.precio || '';
                item.querySelector('.precio-unitario').value = precioUnitario;
                updateTotals();
            });

            cantidadInput.addEventListener('input', () => {
                const option = productoSelect.options[productoSelect.selectedIndex];
                if (option && option.dataset.stock) {
                    if (!validateStock(cantidadInput.value, option.dataset.stock)) {
                        showNotification('La cantidad excede el stock disponible', 'error');
                        cantidadInput.value = option.dataset.stock;
                    }
                }
                updateTotals();
            });
        }
    });

    // Manejar formularios
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            }
        });
    });

    // Inicializar tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', (e) => {
            const tip = document.createElement('div');
            tip.className = 'absolute bg-gray-800 text-white px-2 py-1 rounded text-sm -mt-8 -ml-2 z-50';
            tip.textContent = e.target.dataset.tooltip;
            e.target.appendChild(tip);
        });
        tooltip.addEventListener('mouseleave', (e) => {
            const tip = e.target.querySelector('div');
            if (tip) tip.remove();
        });
    });

    // Configurar observador de cambios para elementos dinámicos
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // ELEMENT_NODE
                        // Reinicializar funcionalidades para nuevos elementos
                        const newItems = node.querySelectorAll('.producto-item');
                        if (newItems.length) {
                            newItems.forEach(item => {
                                // Reinicializar eventos
                            });
                        }
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Exportar funciones para uso global
window.deleteProduct = deleteProduct;
window.showNotification = showNotification;
window.updateTotals = updateTotals;
window.validateForm = validateForm;
window.formatCurrency = formatCurrency;