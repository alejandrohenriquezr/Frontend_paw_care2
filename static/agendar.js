document.addEventListener("DOMContentLoaded", function () {
    const id_clinica = new URLSearchParams(window.location.search).get("id_clinica");
    const horarios_ocupados = [];
    console.log("ID de la clínica:", id_clinica);    
    // 🔥 Verificar si el usuario está autenticado
    //fetch("/api/verificar_sesion")
    //    .then(response => response.json())
    //    .then(data => {
    //        if (!data.autenticado) {
    //            window.location.href = "iniciar_sesion.html";  // 🔥 Redirigir si no está autenticado
    //        }
    //    })
    //    .catch(error => console.error("🚨 Error verificando sesión:", error));

    // 🔥 Evento para reservar cita
    document.getElementById("form_agendar").addEventListener("submit", function (event) {
        event.preventDefault(); // Evitar recarga de la página
        console.log("Formulario enviado!");
        const fecha = document.querySelector(".fecha-seleccionada").dataset.fecha;
        const hora = document.querySelector(".hora-seleccionada").dataset.hora;

        // 🔥 Enviar los datos al backend para guardar la reserva
        fetch("/api/agendar_cita", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id_clinica: id_clinica,
                fecha: fecha,
                hora: hora
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.exito) {
                // 🔥 Bloquear la hora seleccionada en la interfaz
                document.querySelector(`.hora[data-hora='${hora}']`).classList.add("bloqueada");

                // 🔥 Mostrar modal de éxito
                document.getElementById("modal_exito").classList.add("visible");
            } else {
                // 🔥 Mostrar modal de error
                document.getElementById("modal_error").classList.add("visible");
            }
        })
        .catch(error => console.error("🚨 Error al agendar cita:", error));
    });
});
