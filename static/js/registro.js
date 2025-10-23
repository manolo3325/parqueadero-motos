document.addEventListener("DOMContentLoaded", () => {
    const placaInput = document.getElementById("placa");
    const telefonoDiv = document.getElementById("telefonoDiv");
    const nombreDiv = document.getElementById("nombreDiv");
    const resultado = document.getElementById("resultado");
    const botonConsultar = document.getElementById("consultarBtn");
    const botonGuardar = document.getElementById("guardarBtn");
    // Botones de ingreso
    const botonesIngreso = document.getElementById("botonesIngreso");
    const btnHoras = document.getElementById("btnHoras");
    const btnDia = document.getElementById("btnDia");
    const btnMensualidad = document.getElementById("btnMensualidad");

// --- Función para validar placa ---
function validarPlaca(placa) {
    const regex = /^[A-Z]{3}\d{2}[A-Z]?$/;
    return regex.test(placa);
}

// --- Convertir automáticamente a mayúsculas ---
placaInput.addEventListener("input", (e) => {
    e.target.value = e.target.value.toUpperCase();
});

// --- Click en botón Consultar ---
botonConsultar.addEventListener("click", async () => {
    const placa = placaInput.value.trim().toUpperCase();
    resultado.innerHTML = "";
    telefonoDiv.style.display = "none";
    nombreDiv.style.display = "none";
    botonGuardar.style.display = "none";
    botonesIngreso.style.display = "none";

    if (!validarPlaca(placa)) {
        resultado.innerHTML = "<p class='error'>Placa no válida. Ejemplo: ABC12 o ABC12A</p>";
        return;
    }

    try {
        const response = await fetch(`/motos/${placa}`);
        if (response.ok) {
            const data = await response.json();
            resultado.innerHTML = `
                <p><strong>Nombre:</strong> ${data.propietario.nombre}</p>
                <p><strong>Apellidos:</strong> ${data.propietario.apellido}</p>
                <p><strong>Teléfono:</strong> ${data.propietario.telefono}</p>
            `;
            // Mostrar botones de ingreso
            botonesIngreso.style.display = "block";
        } else {
            resultado.innerHTML = "<p>Moto no encontrada. Ingresa el teléfono del propietario.</p>";
            telefonoDiv.style.display = "block";
        }
    } catch (error) {
        console.error("Error al consultar moto:", error);
        resultado.innerHTML = "<p class='error'>Error en la consulta.</p>";
    }
});

// --- Al cambiar teléfono ---
document.getElementById("telefono").addEventListener("input", async (e) => {
    const telefono = e.target.value.trim();
    if (telefono.length < 7) return;

    try {
        const response = await fetch(`/propietario/${telefono}`);
        if (response.ok) {
            const data = await response.json();
            resultado.innerHTML = `
                <p>Propietario existente:</p>
                <p><strong>Nombre:</strong> ${data.nombre}</p>
                <p><strong>Apellidos:</strong> ${data.apellidos}</p>
            `;
            botonGuardar.style.display = "block";
        } else {
            resultado.innerHTML = "<p>Propietario nuevo. Ingresa nombre y apellidos.</p>";
            nombreDiv.style.display = "block";
            botonGuardar.style.display = "block";
        }
    } catch (error) {
        console.error("Error al buscar propietario:", error);
        resultado.innerHTML = "<p class='error'>Error al buscar propietario.</p>";
    }
});

// --- Guardar nuevo propietario y moto ---
botonGuardar.addEventListener("click", async () => {
    const placa = placaInput.value.trim().toUpperCase();
    const telefono = document.getElementById("telefono").value.trim();
    const nombre = document.getElementById("nombre").value.trim();
    const apellidos = document.getElementById("apellidos").value.trim();

    if (!placa || !telefono || !nombre || !apellidos) {
        resultado.innerHTML = "<p class='error'>Todos los campos son obligatorios.</p>";
        return;
    }

    try {
        const response = await fetch("/registrar_moto", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ placa, telefono, nombre, apellidos })
        });

        if (response.ok) {
            resultado.innerHTML = "<p>Moto y propietario registrados correctamente.</p>";
            telefonoDiv.style.display = "none";
            nombreDiv.style.display = "none";
            botonGuardar.style.display = "none";
        } else {
            resultado.innerHTML = "<p class='error'>Error al guardar los datos.</p>";
        }
    } catch (error) {
        console.error("Error al guardar:", error);
        resultado.innerHTML = "<p class='error'>Error al guardar en el servidor.</p>";
    }
});

// --- Funciones para ingreso de moto ---
// --- Ingreso de moto ---
async function registrarIngreso(tipo) {
    const placa = document.getElementById("placa").value.trim().toUpperCase();
    const numCascos = prompt("¿Cuántos cascos deja? (0, 1 o 2):", "0");

    if (!placa) {
        alert("Debes ingresar la placa primero.");
        return;
    }

    try {
        const response = await fetch("/registrar_ingreso", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                placa: placa,
                tipo_cobro: tipo,
                num_cascos: parseInt(numCascos) || 0
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById("resultado").innerHTML = `
                <p class="success">✅ Ingreso registrado con éxito.</p>
                <p><strong>Casillero(s):</strong> ${data.casilleros_asignados.join(", ")}</p>
                <p><strong>Tipo de cobro:</strong> ${data.tipo_cobro}</p>
                <p><strong>Hora de entrada:</strong> ${new Date(data.hora_entrada).toLocaleString()}</p>
            `;
        } else {
            document.getElementById("resultado").innerHTML =
                `<p class="error">❌ ${data.detail || "Error al registrar ingreso"}</p>`;
        }
    } catch (error) {
        console.error("Error en el ingreso:", error);
        document.getElementById("resultado").innerHTML =
            `<p class="error">Error al registrar ingreso.</p>`;
    }
}

// Asignar eventos a los botones
document.getElementById("btnHoras").addEventListener("click", () => registrarIngreso("por_horas"));
document.getElementById("btnDia").addEventListener("click", () => registrarIngreso("por_dia"));
document.getElementById("btnMensualidad").addEventListener("click", () => registrarIngreso("mensualidad"));
});
