let response;
let data;
let usuarioestaautenticado;
//let parametros = await fetch('/api/parametros');;
//recuperar el valor de la variable de sesion fechaSeleccionada
let fechaSeleccionada = sessionStorage.getItem("fechaSeleccionada");
let horaSeleccionada = sessionStorage.getItem("horaSeleccionada");    
let mascotaSeleccionada = sessionStorage.getItem("mascotaSeleccionada");
let id_clinica = sessionStorage.getItem("id_clinica");
//si la variable id_clinica existe en la url y es distinta de vacio, entonces almacenarla en la variable de sesion id_clinica
if (id_clinica == null || id_clinica == "") {   
    const urlParams = new URLSearchParams(window.location.search);
    let id_clinica = urlParams.get("id_clinica") || ""; 
    sessionStorage.setItem("id_clinica", id_clinica);
}

document.addEventListener("DOMContentLoaded", async function () {
/*    response = await fetch('/api/estado_autenticacion');
    data = await response.json();
    data.then(autenticado => {
        console.log("Estado de autenticación:", autenticado);
        if (autenticado) {
            usuarioestaautenticado = true;
        } else {
            usuarioestaautenticado = false;
        }
    });
    console.log("Estado de autenticación:", data.autenticado);
    */
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

//Este script muestra las fechas y horas disponibles para agendar una cita en la clínica seleccionada.
document.addEventListener("DOMContentLoaded", function () {
    const agendarResultados = document.getElementById("agendar_resultados");

   
    // 📌 Obtener ID de la clínica desde la URL
    const urlParams = new URLSearchParams(window.location.search);
    id_clinica = urlParams.get("id_clinica") || "";
    user_info = urlParams.get("user");
    user = user_info || null;
    fecha = urlParams.get("fecha") || null;
    hora = urlParams.get("hora") || null;


    // 📌 Formulario f1
    const formHTML = `
        <div id="f1" class="mt-4 p-4 border rounded bg-gray-100">
            <div id="fechas-container" class="flex space-x-2 mb-4"></div>
            <div id="horas-container" class="hidden flex space-x-2 mt-2"></div>
            <button id="btn-agendar" class="mt-4 px-6 py-3 rounded-full bg-green-500 text-white"></button>
        </div>
    `;
    
    // 🔹 Insertar el formulario en el div agendar_resultados
    agendarResultados.insertAdjacentHTML("afterend", formHTML);

    const fechasContainer = document.getElementById("fechas-container");
    const horasContainer = document.getElementById("horas-container");
    const btnAgendar = document.getElementById("btn-agendar");
    btnAgendar.disabled = true;
    usuarioAutenticado().then(autenticado => {
        console.log("Estado de autenticación:", autenticado);
        if (autenticado) {
            btnAgendar.textContent = "Agendar Cita";
        } else {
            btnAgendar.textContent = "Iniciar Sesión para Agendar";
            btnAgendar.blackgroundColor = "bg-gray-400";
        }
    });

    if (fecha==null || hora==null){
        btnAgendar.disabled = true;
    } else {
        btnAgendar.disabled = false;
    }
    
    // 📅 Generar Fechas (Hoy + 6 días)
    const hoy = new Date();
    const opcionesFecha = { weekday: "long", day: "2-digit", month: "short" };
   //alert(fecha);
   // alert(hora);
   // alert(fecha==null || hora==null);


    for (let i = 0; i < 7; i++) {
        const fecha = new Date();
        fecha.setDate(hoy.getDate() + i);
        const fechaTexto = fecha.toLocaleDateString("es-ES", opcionesFecha);
        fecha.setDate(hoy.getDate() + (i));
        const fechaValor = fecha.toISOString().split("T")[0]; // Formato YYYY-MM-DD

        const btnFecha = document.createElement("button");
        btnFecha.textContent = fechaTexto;
        btnFecha.className = "flex-shrink-0 px-6 py-3 rounded-full bg-[#5A8F99] text-white";
        btnFecha.dataset.fecha = fechaValor;

        btnFecha.addEventListener("click", function () {
            // 📌 Marcar la fecha seleccionada
            document.querySelectorAll("#fechas-container button").forEach(btn => btn.classList.remove("bg-blue-500"));
            btnFecha.classList.add("bg-blue-500");
            //guardar la fecha seleccionada en la variable de sesión fecha
            sessionStorage.setItem("fechaSeleccionada", fechaValor);
            console.log("Fecha seleccionada:", sessionStorage.getItem("fechaSeleccionada"));
            //alert("La fecha seleccionada es: " + fechaValor);
            // 📌 Generar Horas Disponibles
            generarHoras(fechaValor);
        });

        fechasContainer.appendChild(btnFecha);
    }

    function generarHoras(fechaSeleccionada) {
        horasContainer.innerHTML = "";
        horasContainer.classList.remove("hidden");

        correo_cliente = "No hay usuario autenticado";
        //alert("No hay usuario autenticado, por favor inicie sesión para continuar.");
        //}
        
        for (let hora = 10; hora <= 19; hora++) {
            const horaTexto = `${hora.toString().padStart(2, "0")}:00`;
            const btnHora = document.createElement("button");

            btnHora.textContent = horaTexto;
            btnHora.className = "flex-shrink-0 px-6 py-3 rounded-full bg-[#5A8F99] text-white";
            btnHora.dataset.hora = horaTexto;
            const urlParams = new URLSearchParams(window.location.search);
            const id_clinica = urlParams.get("id_clinica") || "";
            esHoraBloqueada(id_clinica, fechaSeleccionada, horaTexto).then(bloqueada => {
/*
            if (esHoraBloqueada(id_clinica, fecha, hora)) {
                //console.log(`La fecha ${fechaSeleccionada} : ${horaTexto} está bloqueada.`);
                btnHora.classList.add("bg-gray-400", "cursor-not-allowed");
                btnHora.disabled = true;
            }else{
*/            
                // 🔴 Bloquear horas 13:00 y 14:00
                if (bloqueada || hora === 13 || hora === 14) {
                    //console.log(`La fecha ${fechaSeleccionada} : ${horaTexto} está bloqueada.`);
                    btnHora.classList.add("bg-gray-400", "cursor-not-allowed");
                    btnHora.disabled = true;
                } else {
                    btnHora.addEventListener("click", function () {
                        document.querySelectorAll("#horas-container button").forEach(btn => btn.classList.remove("bg-blue-500"));
                        btnHora.classList.add("bg-blue-500");
                        //alert(correo_cliente);
                        //almacenar la hora seleccionada en la variable de sesión hora
                        sessionStorage.setItem("horaSeleccionada", horaTexto);
                        console.log("Hora seleccionada:", sessionStorage.getItem("horaSeleccionada"));
                        usuarioAutenticado().then(autenticado => {
                            console.log("Estado de autenticación:", autenticado);
                            if (autenticado) {
                                btnAgendar.disabled = false;
                                insertarCampoMascotas();
                                
                            } else {
                                //  window.location.href = `login?redirect=agendar&${parametros}`;
                                window.location.href = `login?redirect=agendar&fecha=${fechaSeleccionada}&hora=${horaTexto}`;
                                
                            }
                        });
                        
                    });
                }
            });                    
        //}
            
                

            

            horasContainer.appendChild(btnHora);
        }
    }

    async function insertarCampoMascotas() {
        const divMascotas = await crearCampoMascotas();
        horasContainer.insertAdjacentElement("afterend", divMascotas);
        //almacenar la mascota seleccionada en la variable de sesión mascota
        const mascotas = document.getElementById("mis_mascotas");
        mascotas.addEventListener("change", function () {
            const mascotaSeleccionada = mascotas.value;
            sessionStorage.setItem("mascotaSeleccionada", mascotaSeleccionada);
            console.log("Mascota seleccionada:", sessionStorage.getItem("mascotaSeleccionada"));
        });
      }

    // 📌 Verificar autenticación en Google
    async function usuarioAutenticado() {
        try {
            const response = await fetch('/api/estado_autenticacion');
            const data = await response.json();
            console.log("Estado de autenticación:", data.autenticado);
            return data.autenticado;
        } catch (error) {
            console.error('Error al verificar la autenticación:', error);
            return false;
        }
    }

    // 📌 Evento de agendar
    btnAgendar.addEventListener("click", function () {
        const fechaSeleccionada = document.querySelector("#fechas-container .bg-blue-500")?.dataset.fecha;
        const horaSeleccionada = document.querySelector("#horas-container .bg-blue-500")?.dataset.hora;
        const mascotas = document.getElementById("mis_mascotas");
        console.log("Fecha seleccionada:", fechaSeleccionada);
        console.log("Hora seleccionada:", horaSeleccionada);
        if (!fechaSeleccionada || !horaSeleccionada) {
            alert("Por favor, selecciona una fecha y una hora.");
            return;
        }

        // 🔹 Construcción de URL con variables
        const parametros = new URLSearchParams({
            id_clinica: id_clinica,
            fecha: fechaSeleccionada,
            mascota: mascotas.value,
            hora: horaSeleccionada,
            acc:1
        }).toString();

        usuarioAutenticado().then(autenticado => {
            console.log("Estado de autenticación:", autenticado);
            if (autenticado) {
                window.location.href = `agendar?${parametros}`;
            } else {
                window.location.href = `login?redirect=agendar&${parametros}`;
            }
        });
    });

    // 📌 Restaurar selección si el usuario regresa después del login
    const fechaGuardada = urlParams.get("fecha");
    const horaGuardada = urlParams.get("hora");
    const hora2 = horaGuardada.split(":")[0];
    console.log("Fecha guardada:", fechaGuardada);
    console.log("Hora guardada:", hora2);
    if (fechaGuardada) {
        document.querySelector(`[data-fecha="${fechaGuardada}"]`)?.click();
    }
    if (horaGuardada) {
        console.log("activando borton hora ", hora2);
        document.querySelector(`[data-hora="${hora2}"]:00`)?.click();
    }
});

// Función para verificar si una hora está bloqueada
async function esHoraBloqueada(id_clinica, fecha, hora) {
    try {
        const response = await fetch('/api/reservas');
        const reservas = await response.json();
        console.log(reservas); // Verifica el contenido de reservas
        //alert(reservas);
        //alert(id_clinica);
        if (!Array.isArray(reservas)) {
            throw new Error('La respuesta no es un array');
        }
        for (const reserva of reservas) {
            const reservaFechaFormateada = new Date(reserva.fecha.split('-').reverse().join('-')).toISOString().split('T')[0];
            const fechaFormateada = new Date(fecha).toISOString().split('T')[0];
            const horaFormateada = hora.padStart(2, '0') + ':00'; // Asegura que la hora tenga el formato HH:MM
            const reservahoraFormateada = reserva.hora.padStart(5, '0');

            if (reserva.id_clinica === id_clinica && reservaFechaFormateada === fechaFormateada && reservahoraFormateada === horaFormateada && reserva.estado === '1') {
                return true;
            }
        }
        return false;
    } catch (error) {
        console.error('Error al obtener las reservas:', error);
        return false;
    }
}


async function obtenerMascotas() {
    try {
      const response = await fetch('/data/clientes_mascotas.csv');
      const data = await response.text();
      //console.log(data);
      const mascotas = data.split('\n').slice(1).map(line => {
        const [id_clientes_mascotas, correo_cliente, nombre_mascota, fecha_nacimiento, id_especie_raza] = line.split(';');
        if (id_clientes_mascotas && correo_cliente && nombre_mascota && fecha_nacimiento && id_especie_raza) { // Verifica que no haya líneas en blanco
            console.log(id_clientes_mascotas, correo_cliente, nombre_mascota, fecha_nacimiento, id_especie_raza);
            return { id_clientes_mascotas, correo_cliente, nombre_mascota, fecha_nacimiento, id_especie_raza };
        }
      }).filter(mascota => mascota); // Filtra las entradas undefined;
      return mascotas;
    } catch (error) {
      console.error('Error al cargar las mascotas:', error);
      return [];
    }
  }

  async function crearCampoMascotas() {
    const mascotas = await obtenerMascotas();
    const divMascotas = document.createElement('div');
    divMascotas.id = 'mis_mascotas_container';
    divMascotas.className = 'mt-4 p-4 border rounded bg-gray-100';
  
    const selectMascotas = document.createElement('select');
    selectMascotas.id = 'mis_mascotas';
    selectMascotas.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
    mascotas.forEach(mascota => {
      const option = document.createElement('option');
      option.value = mascota.id_clientes_mascotas;
      option.textContent = mascota.nombre_mascota;
      selectMascotas.appendChild(option);
    });
  
    const option = document.createElement('option');
    option.value = '999';
    option.textContent = 'Nueva mascota';
    selectMascotas.appendChild(option);
  
    divMascotas.appendChild(selectMascotas);
    return divMascotas;
  }  