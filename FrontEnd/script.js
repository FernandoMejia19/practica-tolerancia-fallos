// Configuración de endpoints del Backend. 
// Ajustar según el puerto de despliegue local o la IP del Gateway de Kubernetes.
const API_URLS = {
    reservas: '/reservations',
    pagos: '/payments',
    notificaciones: '/notifications'
};

// Listado de eventos precargados que corresponden a los datos insertados en init.sql
const EVENTS = [
    {
        id: 1,
        nombre: 'Concierto de Rock',
        fecha: '2026-08-20',
        lugar: 'Quito',
        precio: 35.00,
        asientos: [1, 2, 3] // IDs de asientos disponibles del concierto en base de datos
    },
    {
        id: 2,
        nombre: 'Festival de Jazz',
        fecha: '2026-09-15',
        lugar: 'Guayaquil',
        precio: 40.00,
        asientos: [4, 5, 6] // IDs de asientos disponibles del festival en base de datos
    }
];

// Estado de la aplicación
let cart = {
    // id_evento: cantidad
};

// Inicializar el carrito a 0 para cada evento
EVENTS.forEach(event => {
    cart[event.id] = 0;
});

// Referencias a elementos del DOM
const eventsGrid = document.getElementById('events-grid');
const cartItemsContainer = document.getElementById('cart-items');
const cartTotalValue = document.getElementById('cart-total-value');
const btnCheckout = document.getElementById('btn-checkout');
const clientNameInput = document.getElementById('client-name');
const clientEmailInput = document.getElementById('client-email');

// Función para renderizar los eventos
function renderEvents() {
    eventsGrid.innerHTML = '';
    
    EVENTS.forEach(event => {
        const card = document.createElement('div');
        card.className = 'event-card';
        
        card.innerHTML = `
            <div>
                <h3 class="event-name">${event.nombre}</h3>
                <p class="event-details">${event.fecha} &bull; ${event.lugar}</p>
            </div>
            <div>
                <p class="event-price">$${event.precio.toFixed(2)} c/u</p>
                <div class="counter-container">
                    <button class="btn-counter" onclick="updateQuantity(${event.id}, -1)">-</button>
                    <span class="counter-value" id="counter-${event.id}">0</span>
                    <button class="btn-counter" onclick="updateQuantity(${event.id}, 1)">+</button>
                </div>
            </div>
        `;
        eventsGrid.appendChild(card);
    });
}

// Función para actualizar la cantidad seleccionada
window.updateQuantity = function(eventId, change) {
    const event = EVENTS.find(e => e.id === eventId);
    if (!event) return;
    
    const currentQty = cart[eventId];
    const newQty = currentQty + change;
    
    // El mínimo es 0, y el máximo es la cantidad de asientos disponibles
    if (newQty >= 0 && newQty <= event.asientos.length) {
        cart[eventId] = newQty;
        document.getElementById(`counter-${eventId}`).textContent = newQty;
        updateCart();
    } else if (newQty > event.asientos.length) {
        showStatus(`No hay más asientos disponibles para ${event.nombre}. Max: ${event.asientos.length}`, 'error');
    }
};

// Función para actualizar la UI del carrito
function updateCart() {
    cartItemsContainer.innerHTML = '';
    let total = 0;
    let hasItems = false;
    
    EVENTS.forEach(event => {
        const qty = cart[event.id];
        if (qty > 0) {
            hasItems = true;
            const subtotal = qty * event.precio;
            total += subtotal;
            
            const itemElement = document.createElement('div');
            itemElement.className = 'cart-item';
            itemElement.innerHTML = `
                <div>
                    <span class="cart-item-name">${event.nombre}</span>
                    <span class="cart-item-meta"> x${qty}</span>
                </div>
                <strong>$${subtotal.toFixed(2)}</strong>
            `;
            cartItemsContainer.appendChild(itemElement);
        }
    });
    
    if (!hasItems) {
        cartItemsContainer.innerHTML = '<p class="empty-cart-msg">El carrito está vacío.</p>';
        btnCheckout.disabled = true;
    } else {
        btnCheckout.disabled = false;
    }
    
    cartTotalValue.textContent = `$${total.toFixed(2)}`;
}

// Función para mostrar mensajes de estado
function showStatus(message, type) {
    // Si no existe el div de estado, lo creamos
    let statusDiv = document.getElementById('status-box');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'status-box';
        document.querySelector('.cart-section').appendChild(statusDiv);
    }
    
    statusDiv.className = `status-msg status-${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    
    // Ocultar mensaje automáticamente si es éxito o error después de 5 segundos
    if (type !== 'loading') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Lógica de checkout / integración con el Backend
btnCheckout.addEventListener('click', async () => {
    const clientName = clientNameInput.value.trim();
    const clientEmail = clientEmailInput.value.trim();

    if (!clientName || !clientEmail) {
        showStatus(
            'Por favor complete su nombre y correo.',
            'error'
        );
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(clientEmail)) {
        showStatus(
            'Por favor ingrese un correo válido.',
            'error'
        );
        return;
    }

    const checkoutItems = [];

    EVENTS.forEach(event => {
        const qty = cart[event.id];

        if (qty > 0) {
            checkoutItems.push({
                event,
                qty
            });
        }
    });

    if (checkoutItems.length === 0) {
        showStatus(
            'Seleccione al menos una entrada.',
            'error'
        );
        return;
    }

    btnCheckout.disabled = true;

    showStatus(
        'Procesando compra en los servidores...',
        'loading'
    );

    const resultados = [];
    const errores = [];

    for (const item of checkoutItems) {
        for (let i = 0; i < item.qty; i++) {
            const seatId = item.event.asientos[i];

            try {
                const response = await fetch(
                    API_URLS.reservas,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            id_asiento: seatId,
                            cliente: clientName,
                            correo: clientEmail,
                            monto: item.event.precio
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    const detalle =
                        typeof data.detail === 'string'
                            ? data.detail
                            : JSON.stringify(data.detail);

                    throw new Error(
                        `HTTP ${response.status}: ${detalle}`
                    );
                }

                resultados.push({
                    evento: item.event.nombre,
                    asiento: seatId,
                    precio: item.event.precio,
                    reserva: data
                });

            } catch (error) {
                errores.push({
                    evento: item.event.nombre,
                    asiento: seatId,
                    mensaje: error.message
                });
            }
        }
    }

    mostrarResultadoCompra(
        resultados,
        errores
    );

    btnCheckout.disabled = false;
});

function mostrarResultadoCompra(
    resultados,
    errores
) {
    let mensaje = '';

    if (resultados.length > 0) {
        mensaje += 'COMPRAS PROCESADAS\n\n';

        resultados.forEach(resultado => {
            const reserva = resultado.reserva;

            const estadoNotificacion =
                reserva.notificacion?.estado
                || 'NO INFORMADO';

            mensaje +=
                `Evento: ${resultado.evento}\n` +
                `Asiento: ${resultado.asiento}\n` +
                `Reserva: #${reserva.id_reserva}\n` +
                `Estado: ${reserva.estado}\n` +
                `Pago: ${reserva.pago?.estado || 'NO INFORMADO'}\n` +
                `Notificación: ${estadoNotificacion}\n\n`;
        });
    }

    if (errores.length > 0) {
        mensaje += 'ERRORES CONTROLADOS\n\n';

        errores.forEach(error => {
            mensaje +=
                `Evento: ${error.evento}\n` +
                `Asiento: ${error.asiento}\n` +
                `Detalle: ${error.mensaje}\n\n`;
        });
    }

    if (
        resultados.length > 0
        && errores.length === 0
    ) {
        showStatus(
            'Compra procesada correctamente.',
            'success'
        );

    } else if (resultados.length > 0) {
        showStatus(
            'La compra se procesó parcialmente.',
            'error'
        );

    } else {
        showStatus(
            'No fue posible procesar la compra.',
            'error'
        );
    }

    alert(mensaje);

    if (resultados.length > 0) {
        EVENTS.forEach(event => {
            cart[event.id] = 0;

            document.getElementById(
                `counter-${event.id}`
            ).textContent = '0';
        });

        clientNameInput.value = '';
        clientEmailInput.value = '';

        updateCart();
    }
}
// Render inicial
renderEvents();
updateCart();
