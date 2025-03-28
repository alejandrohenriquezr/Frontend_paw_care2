document.addEventListener("DOMContentLoaded", async function () {
    const clinicasContainer = document.getElementById("clinicas-container");
    const paginacionContainer = document.getElementById("paginacion");
    const clinicasPorPagina = 3;
    let clinicas = [];
    let paginaActual = 1;

    // 📌 Obtener clínicas cercanas desde JSON
    try {
        const response = await fetch("/static/data/clinicas_cercanas.json");
        clinicas = await response.json();
    } catch (error) {
        console.error("Error al cargar las clínicas:", error);
        return;
    }

    function mostrarClinicas() {
        clinicasContainer.innerHTML = "";
        const inicio = (paginaActual - 1) * clinicasPorPagina;
        const fin = inicio + clinicasPorPagina;
        const clinicasPagina = clinicas.slice(inicio, fin);

        clinicasPagina.forEach(clinica => {
            const card = document.createElement("div");
            card.className = "bg-[#F5F5F5] p-6 rounded-xl border border-neutral-200 shadow-md";

            card.innerHTML = `
                <div class="bg-neutral-200 h-48 rounded-lg mb-4 flex items-center justify-center">
                    <img src="/static/images/id_${clinica.id_clinica}.jpg" alt="${clinica.nombre}" class="h-full w-full object-cover rounded-lg">
                </div>
                <h3 class="text-xl mb-2 text-[#333333]">${clinica.nombre}</h3>
                <p class="text-[#4A4A4A] mb-2"><i class="fa-solid fa-location-dot"></i> A ${clinica.distancia}</p>
                <div class="flex items-center mb-2 text-[#333333]">
                    <i class="fa-solid fa-star text-[#43A047]"></i>
                    <span class="ml-1">${clinica.calificacion} (${clinica.n_calificaciones} reseñas)</span>
                </div>
                <p class="text-[#4A4A4A] mb-2">Especialidades: ${clinica.especialidades}</p>
                <button class="w-full py-2 bg-[#5A8F99] text-white rounded-lg border-2 border-[#5A8F99] shadow-lg hover:bg-[#4F7F88] transition duration-200">Agendar Cita</button>
            `;

            clinicasContainer.appendChild(card);
        });

        actualizarPaginacion();
    }

    function actualizarPaginacion() {
        paginacionContainer.innerHTML = "";
        const totalPaginas = Math.ceil(clinicas.length / clinicasPorPagina);

        for (let i = 1; i <= totalPaginas; i++) {
            const boton = document.createElement("button");
            boton.textContent = i;
            boton.className = `mx-1 px-4 py-2 border ${paginaActual === i ? "bg-[#5A8F99] text-white" : "bg-white text-[#5A8F99]"}`;
            boton.addEventListener("click", () => {
                paginaActual = i;
                mostrarClinicas();
            });
            paginacionContainer.appendChild(boton);
        }
    }

    mostrarClinicas();
});

document.addEventListener("DOMContentLoaded", function () {
    const agendarResultados = document.getElementById("agendar_resultados");
    
    // 📌 Obtener ID de la clínica desde la URL
    const urlParams = new URLSearchParams(window.location.search);
    const id_clinica = urlParams.get("id_clinica") || "";

    // 📌 Formulario f1
    const formHTML = `
        <div id="f1" class="mt-4 p-4 border rounded bg-gray-100">
            <div id="fechas-container" class="flex space-x-2 mb-4"></div>
            <div id="horas-container" class="hidden flex space-x-2 mt-2"></div>
            <button id="btn-agendar" class="mt-4 px-6 py-3 rounded-full bg-green-500 text-white">Agendar</button>
        </div>
    `;
    
    // 🔹 Insertar el formulario en el div agendar_resultados
    agendarResultados.insertAdjacentHTML("afterend", formHTML);

    const fechasContainer = document.getElementById("fechas-container");
    const horasContainer = document.getElementById("horas-container");
    const btnAgendar = document.getElementById("btn-agendar");

    // 📅 Generar Fechas (Hoy + 6 días)
    const hoy = new Date();
    const opcionesFecha = { weekday: "long", day: "2-digit", month: "short" };

    for (let i = 0; i < 7; i++) {
        const fecha = new Date();
        fecha.setDate(hoy.getDate() + i);
        const fechaTexto = fecha.toLocaleDateString("es-ES", opcionesFecha);
        const fechaValor = fecha.toISOString().split("T")[0]; // Formato YYYY-MM-DD

        const btnFecha = document.createElement("button");
        btnFecha.textContent = fechaTexto;
        btnFecha.className = "flex-shrink-0 px-6 py-3 rounded-full bg-[#5A8F99] text-white";
        btnFecha.dataset.fecha = fechaValor;

        btnFecha.addEventListener("click", function () {
            // 📌 Marcar la fecha seleccionada
            document.querySelectorAll("#fechas-container button").forEach(btn => btn.classList.remove("bg-blue-500"));
            btnFecha.classList.add("bg-blue-500");

            // 📌 Generar Horas Disponibles
            generarHoras(fechaValor);
        });

        fechasContainer.appendChild(btnFecha);
    }

    function generarHoras(fechaSeleccionada) {
        horasContainer.innerHTML = "";
        horasContainer.classList.remove("hidden");

        for (let hora = 10; hora <= 19; hora++) {
            const horaTexto = `${hora.toString().padStart(2, "0")}:00`;
            const btnHora = document.createElement("button");

            btnHora.textContent = horaTexto;
            btnHora.className = "flex-shrink-0 px-6 py-3 rounded-full bg-[#5A8F99] text-white";
            btnHora.dataset.hora = horaTexto;

            // 🔴 Bloquear horas 13:00 y 14:00
            if (hora === 13 || hora === 14) {
                btnHora.classList.add("bg-gray-400", "cursor-not-allowed");
                btnHora.disabled = true;
            } else {
                btnHora.addEventListener("click", function () {
                    document.querySelectorAll("#horas-container button").forEach(btn => btn.classList.remove("bg-blue-500"));
                    btnHora.classList.add("bg-blue-500");
                });
            }

            horasContainer.appendChild(btnHora);
        }
    }

    // 📌 Verificar autenticación en Google
    function usuarioAutenticado() {
        return localStorage.getItem("usuario_google") === "autenticado";
    }

    // 📌 Evento de agendar
    btnAgendar.addEventListener("click", function () {
        const fechaSeleccionada = document.querySelector("#fechas-container .bg-blue-500")?.dataset.fecha;
        const horaSeleccionada = document.querySelector("#horas-container .bg-blue-500")?.dataset.hora;

        if (!fechaSeleccionada || !horaSeleccionada) {
            alert("Por favor, selecciona una fecha y una hora.");
            return;
        }

        // 🔹 Construcción de URL con variables
        const parametros = new URLSearchParams({
            id_clinica: id_clinica,
            fecha: fechaSeleccionada,
            hora: horaSeleccionada
        }).toString();

        if (usuarioAutenticado()) {
            window.location.href = `agendar_p2.html?${parametros}`;
        } else {
            window.location.href = `iniciar_sesion.html?redirect=agendar&${parametros}`;
        }
    });

    // 📌 Restaurar selección si el usuario regresa después del login
    const fechaGuardada = urlParams.get("fecha");
    const horaGuardada = urlParams.get("hora");

    if (fechaGuardada) {
        document.querySelector(`[data-fecha="${fechaGuardada}"]`)?.click();
    }
    if (horaGuardada) {
        document.querySelector(`[data-hora="${horaGuardada}"]`)?.click();
    }
});