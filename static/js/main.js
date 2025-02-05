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
    } text-white`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
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

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
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

    // Inicializar datepickers si existen
    const datepickers = document.querySelectorAll('.datepicker');
    if (datepickers.length > 0) {
        datepickers.forEach(datepicker => {
            // Aquí puedes inicializar tu biblioteca de datepicker preferida
        });
    }
});

// Exportar funciones para uso global
window.deleteProduct = deleteProduct;
window.showNotification = showNotification;
window.updateTotals = updateTotals;
window.validateForm = validateForm;