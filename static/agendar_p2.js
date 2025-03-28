document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const fecha = urlParams.get("fecha");
    const hora = urlParams.get("hora");
    const id_clinica = urlParams.get("id_clinica");

    const user = getUserInfo(); // Implementa esta función para obtener la información del usuario autenticado
    const nombreUsuario = user.name;
    const correoUsuario = user.email;
    console.log("Usuario autenticado:", nombreUsuario);
    console.log("correo autenticado:", correoUsuario);
    const mensajeBienvenida = document.getElementById("mensaje_bienvenida");
    mensajeBienvenida.innerHTML = `Hola, ${nombreUsuario}, estás finalizando la reserva.`;

    const formularioMascotas = document.getElementById("formulario_mascotas");
    formularioMascotas.innerHTML = `
        <label for="mis_mascotas">Mis Mascotas:</label>
        <select id="mis_mascotas">
            <option value="nueva">Mi nueva Mascota</option>
        </select>
        <button id="confirmar_cita" disabled>Confirmar cita</button>
    `;

    cargarMascotas(correoUsuario);

    document.getElementById("mis_mascotas").addEventListener("change", function() {
        const seleccion = this.value;
        if (seleccion === "nueva") {
            mostrarFormularioNuevaMascota();
        } else {
            document.getElementById("confirmar_cita").disabled = false;
        }
    });

    document.getElementById("confirmar_cita").addEventListener("click", function() {
        confirmarCita(fecha, hora, id_clinica, document.getElementById("mis_mascotas").value);
    });

    function cargarMascotas(correo) {
        // Implementa la lógica para cargar las mascotas desde clientes_mascotas.csv
        // Filtra por correo y activo == 1
        // Agrega las mascotas al select con id "mis_mascotas"
    }

    function mostrarFormularioNuevaMascota() {
        // Implementa la lógica para mostrar el formulario de nueva mascota
    }

    function confirmarCita(fecha, hora, id_clinica, id_cliente_mascota) {
        // Implementa la lógica para confirmar la cita y guardar en reservas.csv
    }

    function getUserInfo() {
        // Implementa la lógica para obtener la información del usuario autenticado
        return { name: "Nombre de Usuario", email: "usuario@correo.com" }; // Ejemplo
    }
});

function mostrarFormularioNuevaMascota() {
    const formularioMascotas = document.getElementById("formulario_mascotas");
    formularioMascotas.innerHTML += `
        <form id="form_nueva_mascota">
            <input type="hidden" id="correo" value="${correoUsuario}">
            <label for="nombre_mascota">Nombre de la Mascota:</label>
            <input type="text" id="nombre_mascota" maxlength="256">
            <label for="fecha_nacimiento">Fecha de Nacimiento:</label>
            <input type="date" id="fecha_nacimiento">
            <label for="especie">Especie:</label>
            <select id="especie"></select>
            <label for="raza">Raza:</label>
            <select id="raza"></select>
            <label for="dueno">Dueño:</label>
            <input type="text" id="dueno" value="${nombreUsuario}" readonly>
            <label for="n_chip">Número de Chip:</label>
            <input type="number" id="n_chip">
            <button type="button" id="guardar_mascota">Guardar</button>
        </form>
    `;

    cargarEspecies();

    document.getElementById("especie").addEventListener("change", function() {
        cargarRazas(this.value);
    });

    document.getElementById("guardar_mascota").addEventListener("click", function() {
        guardarNuevaMascota();
    });
}

function cargarEspecies() {
    // Implementa la lógica para cargar las especies desde especies.csv
}

function cargarRazas(id_especie) {
    // Implementa la lógica para cargar las razas desde especies_razas.csv filtrando por id_especie
}

function guardarNuevaMascota() {
    // Implementa la lógica para guardar la nueva mascota en clientes_mascotas.csv
    // Muestra el modal de confirmación y actualiza el select de mascotas
}

function confirmarCita(fecha, hora, id_clinica, id_cliente_mascota) {
    // Implementa la lógica para confirmar la cita y guardar en reservas.csv
    // Aquí deberías hacer una solicitud al servidor para guardar la reserva
    fetch('/api/reservas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id_clinica: id_clinica,
            id_cliente_mascota: id_cliente_mascota,
            fecha: fecha,
            hora: hora,
            estado: 0
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = `mis_reservas.html`;
        } else {
            alert("Error al confirmar la cita: " + data.error);
        }
    })
    .catch(error => {
        console.error("Error al confirmar la cita:", error);
        alert("Error al confirmar la cita.");
    });
}