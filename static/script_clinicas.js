let response;
let data;
let usuarioestaautenticado;

//recuperar el valor de las variables de sesión
let fechaSeleccionada = sessionStorage.getItem("fechaSeleccionada");
let fecha= sessionStorage.getItem("fechaSeleccionada");
let horaSeleccionada = sessionStorage.getItem("horaSeleccionada"); 
let hora= sessionStorage.getItem("horaSeleccionada");   
let mascotaSeleccionada = sessionStorage.getItem("mascotaSeleccionada");
let id_clinica = sessionStorage.getItem("id_clinica");
let id_veterinario_seleccionado = urlParams.get("id_veterinario") || ""; 
let ultimoBtnSeleccionado = null;

sessionStorage.setItem("id_veterinario_seleccionado", id_veterinario_seleccionado);
console.log("id_veterinario_seleccionado=", id_veterinario_seleccionado);


//si la variable id_clinica existe en la url y es distinta de vacio, entonces almacenarla en la variable de sesion id_clinica
if (fechaSeleccionada == null || fechaSeleccionada == "") {   
    const urlParams = new URLSearchParams(window.location.search);
    let fechaSeleccionada = urlParams.get("fecha") || ""; 

    console.log("id_veterinario_seleccionado=", id_veterinario_seleccionado);
    sessionStorage.setItem("fechaSeleccionada", fechaSeleccionada);

}

if (horaSeleccionada == null || horaSeleccionada == "") {   
    const urlParams = new URLSearchParams(window.location.search);
    let horaSeleccionada = urlParams.get("hora") || ""; 
    sessionStorage.setItem("horaSeleccionada", horaSeleccionada);
}

if (id_clinica == null || id_clinica == "") {   
    const urlParams = new URLSearchParams(window.location.search);
    let id_clinica = urlParams.get("id_clinica") || ""; 
    sessionStorage.setItem("id_clinica", id_clinica);
}

//almacenar las variables de sesión de JS en PYTHON
fetch('/guardar_datos', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        id_clinica: id_clinica || "",
        fechaSeleccionada: fechaSeleccionada || "",
        horaSeleccionada: horaSeleccionada || "",
        mascotaSeleccionada: mascotaSeleccionada || "",
        id_veterinario_seleccionado: id_veterinario_seleccionado || ""
    })
});

//si al cargar la página el btn_agendar ha sido cliqueado, entonces ejecuta la /api/insertar_reservas
if (sessionStorage.getItem("btnAgendar") == "true") {
    console.log("El botón Agendar ha sido clicado.");
    //fetch('/api/insertar_reservas');
    fetch('/api/pagar');
}else{
    console.log("El botón Agendar no ha sido clicado.");  
}
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
    actualizarTextoBotonAgendar();
    //mostrarClinicas();
});

//Este script muestra las fechas y horas disponibles para agendar una cita en la clínica seleccionada.
document.addEventListener("DOMContentLoaded", function () {
    const agendarResultados = document.getElementById("agendar_resultados");

   
    // 📌 Obtener ID de la clínica desde la URL
    const urlParams = new URLSearchParams(window.location.search);
    user_info = urlParams.get("user");
    user = user_info || null;

    id_clinica = urlParams.get("id_clinica") || "";


    // 📌 Formulario f1
    const formHTML = `
        <div id="f1" class="mt-4 p-4 border rounded bg-gray-100">
            <div id="fechas-container" class="w-full"></div>
            <div id="horas-container" class="hidden flex space-x-2 mt-2"></div>
            <button id="btn-agendar" class="mt-4 px-6 py-3 rounded-full bg-green-500 text-white"></button>
        </div>
    `;
    
    // 🔹 Insertar el formulario en el div agendar_resultados
    agendarResultados.insertAdjacentHTML("afterend", formHTML);

    const fechasContainer = document.getElementById("fechas-container");
    const horasContainer = document.getElementById("horas-container");
    const horaSeleccionada = sessionStorage.getItem("horaSeleccionada");

    const btnAgendar = document.getElementById("btn-agendar");
    btnAgendar.disabled = true;
    usuarioAutenticado().then(autenticado => {
        actualizarTextoBotonAgendar();
        console.log("Estado de autenticación3:", autenticado);
        /*if (autenticado) {
            btnAgendar.textContent = "Pagar Cita";
        } else {
            btnAgendar.textContent = "Iniciar Sesión para Agendar";
            btnAgendar.blackgroundColor = "bg-gray-400";
        }*/
    });

    if (fecha==null || hora==null){
        btnAgendar.disabled = true;
        //cambiamos el color de fondo a gris
        btnAgendar.classList.add("bg-gray-400");
        btnAgendar.classList.remove("bg-green-500");
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
            actualizarTextoBotonAgendar();
            console.log("Fecha seleccionada:", sessionStorage.getItem("fechaSeleccionada"));
            //alert("La fecha seleccionada es: " + fechaValor);
            // 📌 Generar Horas Disponibles
            generarHoras(fechaValor);
        });

        fechasContainer.appendChild(btnFecha);
    }

    async  function generarHoras(fechaSeleccionada) {
    let seleccionGuardada = {};

    await fetch('/api/seleccion_guardada')
        .then(response => response.json())
        .then(data => {
            seleccionGuardada = data;
        });
    
    let paginaActual = 0;
    const veterinariosPorPagina = 3;
    const totalPaginas = Math.ceil(staffData.length / veterinariosPorPagina);

    horasContainer.innerHTML = "";
    horasContainer.classList.remove("hidden");

    // Crear el paginador (solo una vez)
    //si paginador existe, entonces lo eliminamos
    const divExistente = document.getElementById("paginador");
    if (divExistente) {
        divExistente.remove();
    }    
    const paginador = document.createElement('div');
    paginador.id = "paginador";
    paginador.className = "flex flex-wrap justify-center items-center gap-2 my-4";

    // Insertar el paginador justo antes del botón Agendar
    const btnAgendar = document.getElementById("btn-agendar");
    btnAgendar.parentNode.insertBefore(paginador, btnAgendar);

    function mostrarPagina(pagina) {
        paginaActual = pagina;
        horasContainer.innerHTML = "";

        const inicio = pagina * veterinariosPorPagina;
        const fin = inicio + veterinariosPorPagina;
        const veterinariosPagina = staffData.slice(inicio, fin);

        veterinariosPagina.forEach(vet => {
            const contenedorVet = document.createElement("div");
            contenedorVet.className = "flex flex-col bg-gray-100 p-4 rounded shadow-md space-y-4 basis-1/4";

            const divId = document.createElement("div");
            const imgVet = document.createElement("img");
            imgVet.src = `/static/images/vet_${vet.id_veterinario}.jpg`;
            imgVet.alt = `Veterinario ${vet.id_veterinario}`;
            imgVet.className = "w-16 h-16 rounded-full object-cover bg-gray-200";

            const textoVet = document.createElement("span");
            textoVet.innerHTML = `${vet.nombres} ${vet.apellidos}<br>${vet.area_interes}`;
            textoVet.className = "font-bold text-blue-800";

            divId.appendChild(imgVet);
            divId.appendChild(textoVet);

            const divHoras = document.createElement("div");
            divHoras.className = "flex flex-wrap gap-2 justify-end";

            for (let hora = 10; hora <= 19; hora++) {
                const btnIdVet = document.createElement("input");
                btnIdVet.type = "hidden";
                btnIdVet.value = vet.id_veterinario;
                btnIdVet.id = "id_veterinario";
                btnIdVet.name = "id_veterinario";

                const horaTexto = `${hora.toString().padStart(2, "0")}:00`;

                const btnHora = document.createElement("button");
                btnHora.name = `id_veterinario.${vet.id_veterinario}.fecha.${fechaSeleccionada}.hora.${horaTexto}`;
                btnHora.id = `id_veterinario.${vet.id_veterinario}.fecha.${fechaSeleccionada}.hora.${horaTexto}`;
                btnHora.textContent = horaTexto;
                btnHora.className = "px-4 py-2 rounded-full bg-[#5A8F99] text-white";
                btnHora.dataset.hora = horaTexto;

                const fecha_almacenada = sessionStorage.getItem("fechaSeleccionada") || "";
                const hora_almacenada = sessionStorage.getItem("horaSeleccionada") || "";

                sessionStorage.setItem("horaSeleccionada", horaTexto);
                sessionStorage.setItem("fechaSeleccionada", fechaSeleccionada);

                esHoraBloqueada(id_clinica, fechaSeleccionada, horaTexto, vet.id_veterinario).then(bloqueada => {
                    if (
                        bloqueada || hora === 13 || hora === 14 ||
                        (
                            seleccionGuardada &&
                            seleccionGuardada.id_veterinario == vet.id_veterinario &&
                            seleccionGuardada.fechaSeleccionada == fechaSeleccionada &&
                            seleccionGuardada.horaSeleccionada == horaTexto
                        )
                    ) {
                        btnHora.classList.add("bg-gray-400", "cursor-not-allowed");
                        btnHora.disabled = true;
                    
                    } else {
                        btnHora.addEventListener("click", () => {
                            sessionStorage.setItem("id_veterinario", vet.id_veterinario);
                            sessionStorage.setItem("horaSeleccionada", horaTexto);
                            actualizarEstadoBotonAgendar();
                            actualizarTextoBotonAgendar();
                            if (fecha_almacenada === fechaSeleccionada && hora_almacenada === horaTexto) {
                                btnHora.classList.add("bg-gray-400", "cursor-not-allowed");
                                btnHora.disabled = true;
                            } else {
                                // 🔄 Si ya hay una hora seleccionada antes, la desbloqueamos
                                if (ultimoBtnSeleccionado && !ultimoBtnSeleccionado.classList.contains("cursor-not-allowed")) {
                                    ultimoBtnSeleccionado.disabled = false;
                                    ultimoBtnSeleccionado.classList.remove("bg-gray-400", "cursor-not-allowed");
                                    ultimoBtnSeleccionado.classList.remove("bg-blue-500");
                                }

                                // 🔵 Estilizamos la hora actual
                                btnHora.classList.add("bg-blue-500");

                                // 🔁 Guardamos esta como la última hora seleccionada
                                ultimoBtnSeleccionado = btnHora;                                
                                sessionStorage.setItem("horaSeleccionada", horaTexto);
                                sessionStorage.setItem("id_veterinario", vet.id_veterinario);
                                console.log("Hora seleccionada:", horaTexto);
                            }

                        usuarioAutenticado().then(autenticado => {
                            if (autenticado) {
                                btnAgendar.disabled = false;
                                // ejecutamos insertarCampoMascotas()
                                console.log("Estado de autenticación4: ", autenticado);
                                //insertarCampoMascotas();
                            } else {
                                window.location.href = `login?redirect=agendar&fecha=${fechaSeleccionada}&hora=${horaTexto}&id_veterinario=${vet.id_veterinario}`;
                            }
                        });
                        });
                    }
                });

                divHoras.appendChild(btnIdVet);
                divHoras.appendChild(btnHora);
            }

            contenedorVet.appendChild(divId);
            contenedorVet.appendChild(divHoras);
            horasContainer.appendChild(contenedorVet);
        });

        // 🔁 Actualizar paginador
        paginador.innerHTML = "";

        // Botón Anterior
        const btnAnterior = document.createElement("button");
        btnAnterior.textContent = "← Anterior";
        btnAnterior.className = "px-3 py-1 rounded bg-gray-200 hover:bg-gray-300";
        btnAnterior.disabled = pagina === 0;
        btnAnterior.addEventListener("click", () => mostrarPagina(pagina - 1));
        paginador.appendChild(btnAnterior);

        // Botones numerados
        for (let i = 0; i < totalPaginas; i++) {
            const btnPagina = document.createElement("button");
            btnPagina.textContent = i + 1;
            btnPagina.className = `px-3 py-1 rounded ${i === pagina ? 'bg-blue-500 text-white' : 'bg-gray-100'}`;
            btnPagina.addEventListener("click", () => mostrarPagina(i));
            paginador.appendChild(btnPagina);
        }

        // Botón Siguiente
        const btnSiguiente = document.createElement("button");
        btnSiguiente.textContent = "Siguiente →";
        btnSiguiente.className = "px-3 py-1 rounded bg-gray-200 hover:bg-gray-300";
        btnSiguiente.disabled = pagina === totalPaginas - 1;
        btnSiguiente.addEventListener("click", () => mostrarPagina(pagina + 1));
        paginador.appendChild(btnSiguiente);
    }

    mostrarPagina(0); // Cargar la primera página
    }
   
    
    async function insertarCampoMascotas() {
        //verificamos si el div de mascotas ya existe, si existe lo eliminamos
        // ✅ Eliminar el div anterior si ya existe
        const divExistente = document.getElementById("mis_mascotas_container");
        if (divExistente) {
            divExistente.remove();
        }
        const divCamposSelect = document.createElement('div');
        divCamposSelect.id = 'Container-CamposSelect';
        divCamposSelect.className = 'flex flex-col md:flex-row gap-6';

        const divMascotas = await crearCampoMascotas();
        //const divSelectEspecialidadPrestacionPrecios = await crearCampoSelectEspecialidadPrestacionPrecios();
        horasContainer.insertAdjacentElement("afterend", divMascotas);
        //divMascotas.insertAdjacentElement("afterend", divSelectEspecialidadPrestacionPrecios);
        //almacenar la mascota seleccionada en la variable de sesión mascota
        const mascotas = document.getElementById("mis_mascotas");
        mascotaSeleccionada = mascotas.value;
        fetch('/almacenar_mascota', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mascotaSeleccionada: mascotaSeleccionada
            })
        });

        mascotas.addEventListener("change", function () {
            
            mascotaSeleccionada = mascotas.value;
            sessionStorage.setItem("mascotaSeleccionada", mascotaSeleccionada);
            console.log("Mascota seleccionada:", sessionStorage.getItem("mascotaSeleccionada"));
            //debo gardar la mascota seleccionada en una variable sesión y entrregarla a python
            fetch('/almacenar_mascota', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mascotaSeleccionada: mascotaSeleccionada
                })
            });
            const valor = mascotaSeleccionada;
            let contenedor = document.getElementById('campos-nueva-mascota');
        
            // Si no existe el contenedor, lo creamos y lo agregamos después del select
            if (!contenedor) {
                contenedor = document.createElement('div');
                contenedor.id = 'campos-nueva-mascota';
                contenedor.className = 'w-full';
        
                // insertarlo justo después del select
                const selectMascotas = document.getElementById('mis_mascotas');
                selectMascotas.parentNode.insertBefore(contenedor, selectMascotas.nextSibling);
            }
        
            contenedor.innerHTML = ''; // limpiar contenido previo

            if (valor === '999') {
                guardarCamposNuevaMascotaEnSesion();
                //en este punto debo crear una nueva variable de sesion en py que se llame crear_mascota con valor 1
                
                fetch('/api/crea_variable_sesion_mascota', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        crear_mascota: 1
                    })
                }
                )
                //y luego hacer un fetch a la api /api/especies para obtener las especies
                //y luego crear los campos para crear una nueva mascota


                fetch('/api/especies')
                    .then(res => res.json())
                    .then(especies => {
                        contenedor.innerHTML = 
                        //insertamos un campo oculto llamado crear_mascota con el valor 1

                        `
                            <input type="hidden" id="crear_mascota" value="1" />
                            <input type="text" id="nombre_mascota" placeholder="Nombre de la mascota" class="input" />
                            <input type="date" id="fecha_nacimiento" class="input" />
                            

                            <select id="sexo_mascota" class="input">
                                <option value="">Sexo</option>
                                <option value="Macho">Macho</option>
                                <option value="Hembra">Hembra</option>
                            </select>
                            <input type="number" step="0.1" min="0" max="1000" id="peso_mascota" placeholder="Peso (kg)" class="input" />
                            <select id="especie_mascota" class="input">
                                <option value="">Selecciona especie</option>
                                ${especies.map(e => `<option value="${e.id_especie}">${e.especie}</option>`).join('')}
                            </select>
                            <select id="raza_mascota" class="input" disabled><option value="">Selecciona una especie primero</option></select>
                        `;
        
                        document.getElementById('especie_mascota').addEventListener('change', function () {
                            const id_especie = this.value;
                            fetch(`/api/razas?id_especie=${id_especie}`)
                                .then(res => res.json())
                                .then(razas => {
                                    const razaSelect = document.getElementById('raza_mascota');
                                    razaSelect.innerHTML = razas.map(r => `<option value="${r.id_especie_raza}">${r.nombre_raza}</option>`).join('');
                                    razaSelect.disabled = false;
                                });
                        });
        
                        ['nombre_mascota', 'fecha_nacimiento', 'sexo_mascota', 'peso_mascota'].forEach(id => {
                            document.getElementById(id).addEventListener('change', () => {
                                fetch('/api/sesion/nueva_mascota', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        campo: id,
                                        valor: document.getElementById(id).value
                                    })
                                });
                            });
                        });
        
                        document.getElementById('especie_mascota').addEventListener('change', () => {
                            fetch('/api/sesion/nueva_mascota', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    campo: 'especie_mascota',
                                    valor: document.getElementById('especie_mascota').value
                                })
                            });
                        });
        
                        document.getElementById('raza_mascota').addEventListener('change', () => {
                            fetch('/api/sesion/nueva_mascota', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    campo: 'raza_mascota',
                                    valor: document.getElementById('raza_mascota').value
                                })
                            });
                        });
                    });
            } else {
                contenedor.innerHTML = '';
            }

        });
        return divCamposSelect;
    }
    document.getElementById('mis_mascotas').addEventListener('change', function () {
    const valor = this.value;
    sessionStorage.setItem("mascotaSeleccionada", valor);  // <-- justo donde haces `valor = this.value`

    let contenedor = document.getElementById('campos-nueva-mascota');

    // Si no existe el contenedor, lo creamos y lo agregamos después del select
    if (!contenedor) {
        contenedor = document.createElement('div');
        contenedor.id = 'campos-nueva-mascota';
        contenedor.className = 'grid grid-cols-2 gap-4 mt-4';

        // insertarlo justo después del select
        const selectMascotas = document.getElementById('mis_mascotas');
        selectMascotas.parentNode.insertBefore(contenedor, selectMascotas.nextSibling);
    }

    contenedor.innerHTML = ''; // limpiar contenido previo

    if (valor === '999') {
        guardarCamposNuevaMascotaEnSesion();

        fetch('/api/especies')
            .then(res => res.json())
            .then(especies => {
                contenedor.innerHTML = `
                    <input type="text" id="nombre_mascota" placeholder="Nombre de la mascota" class="input" />
                    <input type="date" id="fecha_nacimiento" class="input" />
                    <select id="sexo_mascota" class="input">
                        <option value="">Sexo</option>
                        <option value="Macho">Macho</option>
                        <option value="Hembra">Hembra</option>
                    </select>
                    <input type="number" step="0.1" min="0" max="1000" id="peso_mascota" placeholder="Peso (kg)" class="input" />
                    <select id="especie_mascota" class="input">
                        <option value="">Selecciona especie</option>
                        ${especies.map(e => `<option value="${e.id_especie}">${e.especie}</option>`).join('')}
                    </select>
                    <select id="raza_mascota" class="input" disabled><option value="">Selecciona una especie primero</option></select>
                `;

                document.getElementById('especie_mascota').addEventListener('change', function () {
                    const id_especie = this.value;
                    fetch(`/api/razas?id_especie=${id_especie}`)
                        .then(res => res.json())
                        .then(razas => {
                            const razaSelect = document.getElementById('raza_mascota');
                            razaSelect.innerHTML = razas.map(r => `<option value="${r.id_raza}">${r.raza}</option>`).join('');
                            razaSelect.disabled = false;
                        });
                });


                document.getElementById('especie_mascota').addEventListener('change', () => {
                    fetch('/api/sesion/nueva_mascota', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            campo: 'especie_mascota',
                            valor: document.getElementById('especie_mascota').value
                        })
                    });
                });
 
                document.getElementById('raza_mascota').addEventListener('change', () => {
                    fetch('/api/sesion/nueva_mascota', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            campo: 'raza_mascota',
                            valor: document.getElementById('raza_mascota').value
                        })
                    });

                });
                ['nombre_mascota', 'fecha_nacimiento', 'sexo_mascota', 'peso_mascota', 'raza_mascota', 'especie_mascota'].forEach(id => {
                    document.getElementById(id).addEventListener('change', () => {
                        fetch('/api/sesion/nueva_mascota', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                campo: id,
                                valor: document.getElementById(id).value
                            })
                        });
                    });
                });

            });
    } else {
        contenedor.innerHTML = '';
    }
});

    // 📌 Verificar autenticación en Google
    async function usuarioAutenticado() {
        try {
            const response = await fetch('/api/estado_autenticacion');
            const data = await response.json();
            console.log("Estado de autenticación5:", data.autenticado);
            sessionStorage.setItem("usuarioAutenticado", data.autenticado);

            insertarCampoMascotas();
            
            return data.autenticado;
        } catch (error) {
            console.error('Error al verificar la autenticación:', error);
            return false;
        }
    }

    // 📌 Evento de agendar
    
    // 📌 Restaurar selección si el usuario regresa después del login
    fechaGuardada = urlParams.get("fecha");
    if (!fechaGuardada) {
        fechaGuardada = sessionStorage.getItem("fechaSeleccionada");
    }
    console.log("Fecha guardada:", fechaGuardada);
    horaGuardada = urlParams.get("hora");
    if (!horaGuardada) {
        horaGuardada = sessionStorage.getItem("horaSeleccionada");
    }
    if (horaGuardada) {
        hora2 = horaGuardada.split(":")[0];
        console.log("Hora2 guardada:", hora2);
    }


    if (fechaGuardada) {
        document.querySelector(`[data-fecha="${fechaGuardada}"]`)?.click();
    }
    if (horaGuardada) {
        console.log("activando borton hora ", hora2);
        document.querySelector(`[data-hora="${hora2}:00"]`)?.click();
    
    }

    function actualizarEstadoBotonAgendar() {
        const autenticado = sessionStorage.getItem("usuarioAutenticado") === "true";
        const horaSeleccionada = sessionStorage.getItem("horaSeleccionada");
        //const precio = document.getElementById("precio")?.value || 0;
        const precioVisible = sessionStorage.getItem("precio_visible");
        if (precioVisible == null || precioVisible == "") {
            const mostrandoPrecio = false;
        }else{
            const mostrandoPrecio = true
        }    
        const btnAgendar = document.getElementById("btn-agendar");
        
        if (autenticado && horaSeleccionada && mostrandoPrecio) {   
            btnAgendar.disabled = false;
            btnAgendar.classList.remove("bg-gray-400");
            btnAgendar.classList.add("bg-green-500");

        } else {
            btnAgendar.disabled = true;
            btnAgendar.classList.add("bg-gray-400");
            btnAgendar.classList.remove("bg-green-500");
            
        }
    }
    actualizarTextoBotonAgendar();
});

function verificarHabilitacionBoton() {
    const precio = parseFloat(document.getElementById("precio")?.value || 0);
    const hora = sessionStorage.getItem("horaSeleccionada");
    const usuarioAutenticado = sessionStorage.getItem("usuarioAutenticado") === "true";

    const btn = document.getElementById("btn-agendar");

    
    // Comprobamos que se esté mostrando un precio distinto de vacío o cero
    // si existe la variable de sección precio_visible y es distinta de 0
    const precio_formateado = sessionStorage.getItem("precio_formateado");
    
    console.log("precio_formateado:", precio_formateado);
    // entonces creamos ma variable mostrando precio con true, en cado contratio la creamos con false
    if (precio_formateado == null || precio_formateado == "") {
        const mostrandoPrecio = false;
    }else{
        const mostrandoPrecio = true;
    }

    //const mostrandoPrecio = precioVisible && precioVisible !== "$0" && precioVisible !== "";
    console.log("mostrandoPrecio:", mostrandoPrecio);
    console.log("usuarioAutenticado:", usuarioAutenticado);
    console.log("hora:", hora);
    console.log("precio:", precio);
    if (usuarioAutenticado && hora && (precio > 0)) {
        console.log("Habilitamos el botón agendar.");
        btn.disabled = false;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
        btn.removeEventListener("click", handleAgendarClick);
        btn.addEventListener("click", handleAgendarClick);
    } else {
        console.log("Deshabilitamos el botón agendar.");
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
    }

    function handleAgendarClick() {
        const horaSeleccionada = document.querySelector(".btn-hora.active");
        const valorTexto = document.getElementById("precio")?.textContent || "";
        const valorNumerico = parseFloat(valorTexto.replace(/[^\d.]/g, ""));
        guardarCamposNuevaMascotaEnSesion();

        if (!usuarioAutenticado) {
          $("#modal-login").modal("show");
          return;
        }
      
        if (horaSeleccionada && valorNumerico > 0) {
          console.log("Redirigiendo a /api/pagar");
          window.location.href = "/api/pagar";
        }
      }
    return true;
}

function actualizarTextoBotonAgendar() {
    const btnAgendar = document.getElementById("btn-agendar");
    const fecha = sessionStorage.getItem("fechaSeleccionada");
    const hora = sessionStorage.getItem("horaSeleccionada");
    const especialidad = document.getElementById("selectEspecialidad")?.value;
    const precio = parseFloat(document.getElementById("precio")?.value || 0);
    const autenticado = sessionStorage.getItem("usuarioAutenticado") === "true";
    const precio_formateado = sessionStorage.getItem("precio_formateado");
    if (precio_formateado == null || precio_formateado == "") {
        mostrandoPrecio = false;
    }else{
        mostrandoPrecio = true;
    }    
    btnAgendar.classList.add("bg-gray-400");
    btnAgendar.classList.remove("bg-green-500");
    btnAgendar.disabled = true;
    if (!fecha) {
        btnAgendar.textContent = "Paso 1: Selecciona una fecha";
    } else if (!hora) {
        btnAgendar.textContent = "Paso 2: Selecciona una hora";
    } else if (!especialidad || especialidad === "0") {

        btnAgendar.textContent = "Paso 3: Selecciona una especialidad";
    } else if (mostrandoPrecio) {
        btnAgendar.textContent = "Paso 4: Pagar cita";
        btnAgendar.classList.remove("bg-gray-400");
        btnAgendar.classList.add("bg-green-500");
        btnAgendar.disabled = false;
    } else {
        btnAgendar.textContent = "Iniciar Sesión para Agendar";
    }
}


// Función para verificar si una hora está bloqueada
async function esHoraBloqueada(id_clinica, fecha, hora, id_veterinario) {
    try {
        // ejecutamos la /api/reservas sólo la primera vez que se carga la página
        //y luego guardamos el resultado en una variable de sesión
        //si la variable de sesión reservas no existe, entonces la creamos
        //si la variable de sesión reservas existe, entonces la usamos
        if (sessionStorage.getItem("reservas") == null) {
            const response = await fetch('/api/reservas');
            //const reservas = await response.json();
            reservas = await response.json();
            sessionStorage.setItem("reservas", JSON.stringify(reservas));
            console.log("reservas creada=", reservas); // Verifica el contenido de reservas
        }else{
            //const reservas = JSON.parse(sessionStorage.getItem("reservas"));
            reservas = JSON.parse(sessionStorage.getItem("reservas"));
            console.log("reservas existente=", reservas); // Verifica el contenido de reservas
        }

        console.log("id_veterinario=", id_veterinario); // Verifica el contenido de reservas
        //pasamos id_veterinario a string
        id_veterinario = String(id_veterinario);
        id_veterinario_seleccionado = String(id_veterinario_seleccionado);
        //console.log("En esHoraBloqueda id_veterinario=", id_veterinario); // Verifica el contenido de reservas
        //console.log("en esHoraBloqueada id_veterinario_seleccionado=", id_veterinario_seleccionado); // Verifica el contenido de reservas
        //console.log(reservas); // Verifica el contenido de reservas
        //alert(reservas);
        //alert(id_clinica);

        for (const reserva of reservas) {
            const reservaFechaFormateada = new Date(reserva.fecha.split('-').reverse().join('-')).toISOString().split('T')[0];
            const fechaFormateada = new Date(fecha).toISOString().split('T')[0];
            const horaFormateada = hora.padStart(2, '0') + ':00'; // Asegura que la hora tenga el formato HH:MM
            const reservahoraFormateada = reserva.hora.padStart(5, '0');
            const id_veterinario_reserva = String(reserva.medico_que_atendio);
            /*console.log("reserva.hora=", reserva.hora);
            console.log("horaFormateada=", horaFormateada);
            console.log("reservahoraFormateada=", reservahoraFormateada);   */
            console.log("reserva.id_clinica=", reserva.id_clinica, 
                " id_clinica=", id_clinica, 
                " reservaFechaFormateada=", reservaFechaFormateada, 
                " fechaFormateada=", fechaFormateada, 
                " reservahoraFormateada=", reservahoraFormateada, 
                " horaFormateada=", horaFormateada, 
                " reserva.estado=", reserva.estado, 
                " id_veterinario=", id_veterinario, 
                " id_veterinario_reserva=", id_veterinario_reserva); // Verifica el contenido de reservas
                //OJO: debo agregar && reserva.estado === '1' para que no se muestre la hora bloqueada si la reserva está cancelada
                if (
                    String(reserva.id_clinica) === String(id_clinica) &&
                    reservaFechaFormateada === fechaFormateada &&
                    reservahoraFormateada === horaFormateada &&
                    String(reserva.medico_que_atendio) === String(id_veterinario) &&
                    String(reserva.estado) === "1"
                ) {
                    console.log("Bloqueada por reserva:", reserva);
                    console.log("La hora está bloqueada para el veterinario seleccionado.");
                    console.log("reserva.id_clinica=", reserva.id_clinica, " id_clinica=", id_clinica, " reservaFechaFormateada=", reservaFechaFormateada, " fechaFormateada=", fechaFormateada, " reservahoraFormateada=", reservahoraFormateada, " horaFormateada=", horaFormateada, " reserva.estado=", reserva.estado, " id_veterinario=", id_veterinario, " id_veterinario_reserva=", id_veterinario_reserva); // Verifica el contenido de reservas
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
    //divMascotas.className = 'mt-4 p-4 border rounded bg-gray-100';
    //divMascotas.className = 'flex flex-col md:flex-row gap-6';
    divMascotas.className = 'w-full';
    
  
    const selectMascotas = document.createElement('select');
    selectMascotas.id = 'mis_mascotas';
    selectMascotas.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
    mascotas.forEach(mascota => {
      const option = document.createElement('option');
      option.value = mascota.id_clientes_mascotas;
      option.textContent = mascota.nombre_mascota;
      selectMascotas.appendChild(option);
    });
  
    if (mascotas.length > 0) {
        mascotaSeleccionada = mascotas[0].id_clientes_mascotas; // Selecciona la primera mascota por defecto
        }
    else {
        mascotaSeleccionada = 999; // Selecciona la opción "Seleccione una mascota" por defecto

    }
    console.log("mascotaSeleccionada=", mascotaSeleccionada); // Verifica el contenido de df_precios
    fetch('/almacenar_mascota', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            mascotaSeleccionada: mascotaSeleccionada
        })
    });


    const option = document.createElement('option');
    option.value = '999';
    option.textContent = 'Nueva mascota';
    selectMascotas.appendChild(option);
  
    divMascotas.appendChild(selectMascotas);
    
    // Agregamos el select de especialidades_clinica
    id_veterinario= sessionStorage.getItem("id_veterinario");
    if (id_veterinario == null || id_veterinario == "") {   
        const urlParams = new URLSearchParams(window.location.search);
        id_veterinario = urlParams.get("id_veterinario") || ""; 
    }
    const response_especialidades = await fetch('/api/especialidades_clinica?id_veterinario=' + id_veterinario);

    
    const df_especialidades = await response_especialidades.json();
    console.log("df_especialidades=", df_especialidades); // Verifica el contenido de df_precios
    const selectEspecialidad = document.createElement('select');
    selectEspecialidad.id = 'selectEspecialidad';
    selectEspecialidad.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
    //creamos un dataframe llamado especialidades, que se obtinene filtrando el df_precios para los valores unicos de id_especialidad
    //y luego lo convertimos a un array de objetos
    const especialidades = df_especialidades.map(precio => {
        return { id_especialidad: precio.id_especialidad, especialidad: precio.especialidad };
    });

  
    // Al selectEspecialidad le creamos un option con el valor 0 y el texto "Seleccione una especialidad"
    const option0 = document.createElement('option');
    option0.value = '0';
    option0.textContent = 'Seleccione una especialidad';
    selectEspecialidad.appendChild(option0);

    especialidades.forEach(fila_especialidad => {
        const option = document.createElement('option');
        option.value = fila_especialidad.id_especialidad;
        option.textContent = fila_especialidad.especialidad;
        selectEspecialidad.appendChild(option);
    });
    divMascotas.appendChild(selectEspecialidad);


    //Agregamos el sleect de prestaciones_clinica
    //a la prestaciones_clinica le tenemos que entregar el valor seleccionado de selectEspecialidad
    //cuando se seleccione una especialidad, se debe cargar el select de prestaciones_clinica
    //y filtrar por el id_especialidad seleccionado
    selectEspecialidad.addEventListener('change', async function () {
        const id_especialidad = selectEspecialidad.value;
        console.log("id_especialidad=", id_especialidad); // Verifica el contenido de df_precios
        actualizarTextoBotonAgendar();
        // Eliminar el selectprestaciones si ya existe
        let oldSelect = document.getElementById('selectprestaciones');
        if (oldSelect) {
            oldSelect.remove();
        }
        //removemos el valor_prestacion
        let oldDivValor = document.getElementById('valor_prestacion');
        if (oldDivValor) {
            oldDivValor.remove();       
        }

        //removemos el input precio
        let oldInputPrecio = document.getElementById('precio');
        if (oldInputPrecio) {
            oldInputPrecio.remove();       
        }
        //si el id_especialidad es distinto de 0, entonces cargamos el select de prestaciones_clinica
        
        // si selectprestaciones existe, lo eliminamos
    // Solo crear el nuevo select si se seleccionó una especialidad válida
        if (id_especialidad !== '0') {
            let selectprestaciones = document.createElement('select');
            selectprestaciones.id = 'selectprestaciones';
            selectprestaciones.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
            
        
        
            const response_prestaciones = await fetch('/api/prestaciones_clinica?id_especialidad=' + id_especialidad    + '&id_veterinario=' + id_veterinario);
        
            const df_prestaciones = await response_prestaciones.json();
            //guardamos df_prestaciones en una variable de secion
            sessionStorage.setItem("df_prestaciones", JSON.stringify(df_prestaciones));
            
            console.log("df_prestaciones=", df_prestaciones); // Verifica el contenido de df_precios
            //const selectprestaciones = document.createElement('select');
            
            //creamos un dataframe llamado especialidades, que se obtinene filtrando el df_precios para los valores unicos de id_especialidad
            //y luego lo convertimos a un array de objetos
            const prestaciones = df_prestaciones.map(precio => {
                return { id_prestacion: precio.id_prestacion, prestacion: precio.prestacion };
            });
            fila=0;
            prestaciones.forEach(fila_prestaciones => {
                const option = document.createElement('option');
                //option.value = fila_prestaciones.id_prestacion;
                option.value = fila;
                fila++;
                option.textContent = fila_prestaciones.prestacion;
                selectprestaciones.appendChild(option);
            });
            divMascotas.appendChild(selectprestaciones);
            // mostramos el campo valor del selectprestaciones
            const divValor = document.createElement('div');
            divValor.id = 'valor_prestacion';
            divValor.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
            //el precio es igual al valor de la prestacion seleccionada
            const precio = df_prestaciones[0].valor;
            fetch('/almacenar_precio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ precio: precio })
                })
                .then(response => response.json())
                .then(data => {
                console.log('Respuesta del servidor:', data);
                // podrías redirigir si quieres
                // window.location.href = data.url_redireccion;
                });
            verificarHabilitacionBoton()
            // mostramos el precio con formato de punto para separaciónb de miles
            // y sin decimales
            const precio_formateado = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 0 }).format(precio);
            
            divValor.textContent = 'Valor: $' + precio_formateado;
            sessionStorage.setItem("precio_formateado", precio_formateado);
            divMascotas.appendChild(divValor);
            //Agregamos un campo oculto llamado precio con el valor de precio
            const inputPrecio = document.createElement('input');
            inputPrecio.type = 'hidden';
            inputPrecio.id = 'precio';
            inputPrecio.name = 'precio';
            inputPrecio.value = precio;
            divMascotas.appendChild(inputPrecio);
            verificarHabilitacionBoton();
            actualizarTextoBotonAgendar();

        }
        //si selectprestaciones cambia, entonces Obtenermos el valor desde df_prestaciones (campo valor del js), donde el id_prestacion es igual al valor del selectprestaciones
        // y lo mostramos en el divValor
        selectprestaciones.addEventListener('change', async function () {
            const id_prestacion = selectprestaciones.value;
            console.log("id_prestacion=", id_prestacion); // Verifica el contenido de df_precios
            //obtenermos df_prestaciones desde la variable de sesion
            const df_prestaciones = JSON.parse(sessionStorage.getItem("df_prestaciones"));
            // Eliminar el divValor si ya existe
            let oldDivValor = document.getElementById('valor_prestacion');
            if (oldDivValor) {
                oldDivValor.remove();       
            }
            //removemos el input precio
            let oldInputPrecio = document.getElementById('precio');
            if (oldInputPrecio) {
                oldInputPrecio.remove();       
            }
            //si el id_prestacion es distinto de 0, entonces cargamos el valor de la prestacion
            if (id_prestacion) {
                const precio = df_prestaciones[id_prestacion].valor;
                console.log("precio=", precio); // Verifica el contenido de df_precios
                //const selectprestaciones = document.createElement('select');
                
                //creamos un dataframe llamado especialidades, que se obtinene filtrando el df_precios para los valores unicos de id_especialidad
                //y luego lo convertimos a un array de objetos
                //const valor = df_valor[0].valor;
                // mostramos el precio con formato de punto para separaciónb de miles
                // y sin decimales
                const divValor = document.createElement('div');
                divValor.id = 'valor_prestacion';
                divValor.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
                            
                const precio_formateado = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 0 }).format(precio);
                
                divValor.textContent = 'Valor: $' + precio_formateado;
                divMascotas.appendChild(divValor);
                sessionStorage.setItem("precio_formateado", precio_formateado);
                const inputPrecio = document.createElement('input');
                inputPrecio.type = 'hidden';
                inputPrecio.id = 'precio';
                inputPrecio.name = 'precio';
                inputPrecio.value = precio;
                divMascotas.appendChild(inputPrecio);
                verificarHabilitacionBoton();
            }
        });
        
    })

    return divMascotas;
  }  

  async function crearCampoSelectEspecialidadPrestacionPrecios() {
    const response = await fetch('/api/precios');
    const df_precios = await response.json();
    //const divCampos = document.createElement('div');
    //divCampos.id = 'SelectEspecialidadPrestacionPrecios';
    //divCampos.className = 'flex flex-col gap-4 md:w-2/3';
    //divMascotas.className = 'flex flex-col md:flex-row gap-6';
    const divEspecialidad = document.createElement('div');
    // agregamos       <label for="selectEspecialidad">Especialidad:</label>
    //const labelEspecialidad = document.createElement('label');
    //labelEspecialidad.setAttribute('for', 'selectEspecialidad');
    //labelEspecialidad.textContent = 'Especialidad:';
    //divEspecialidad.appendChild(labelEspecialidad);
    const selectEspecialidad = document.createElement('select');
    selectEspecialidad.id = 'selectEspecialidad';
    selectEspecialidad.className = 'px-4 py-2 border border-neutral-300 rounded-lg text-[#2E2E2E]';
    //creamos un dataframe llamado especialidades, que se obtinene filtrando el df_precios para los valores unicos de id_especialidad
    //y luego lo convertimos a un array de objetos
    const especialidades = df_precios.map(precio => {
        return { id_especialidad: precio.id_especialidad, especialidad: precio.especialidad };
    });
    //filtramos los valores unicos de id_especialidad

    especialidades.forEach(fila_especialidad => {
        const option = document.createElement('option');
        option.value = fila_especialidad.id_especialidad;
        option.textContent = fila_especialidad.especialidad;
        selectEspecialidad.appendChild(option);
    });
  
  
    divEspecialidad.appendChild(selectEspecialidad);
    //divCampos.appendChild(divEspecialidad);
    return divEspecialidad;
  }    

  document.addEventListener("click", function (event) {
    if (event.target && event.target.id === "btn-agendar") {
        console.log("Botón Agendar clicado");
        const fechaSeleccionada = document.querySelector("#fechas-container .bg-blue-500")?.dataset.fecha;
        const id_veterinario = sessionStorage.getItem("id_veterinario");

        const mascotas = document.getElementById("mis_mascotas");

        const precio= document.getElementById("precio").value;
        //actualizarEstadoBotonAgendar();
        console.log("precio:", precio);
        
        //le entregamos precio a app.py

        //si el precio es distinto de 0, entonces lo guardamos en la variable de sesión precio
        if (precio != 0) {
            sessionStorage.setItem("precio", precio);
            console.log("precio guardado en la variable de sesión:", sessionStorage.getItem("precio"));
        } else {
            sessionStorage.setItem("precio", 0);
            console.log("precio guardado en la variable de sesión:", sessionStorage.getItem("precio"));
        }

        console.log("id_veterinario en la hora seleccionada:", id_veterinario, ", Fecha seleccionada final:", fecha, ", Hora seleccionada: final", hora);

        mascotaSeleccionada = mascotas.value;
        sessionStorage.setItem("mascotaSeleccionada", mascotaSeleccionada);
        console.log("Mascota seleccionada:", sessionStorage.getItem("mascotaSeleccionada"));


        // 🔹 Construcción de URL con variables
        const parametros = new URLSearchParams({
            id_clinica: id_clinica,
            fecha: fecha,
            mascota: mascotas.value,
            hora: hora,
            id_veterinario: id_veterinario,
            precio: precio,
            acc:1
        }).toString();
        window.location.href = '/api/pagar';
        /*
        usuarioAutenticado().then(autenticado => {
            console.log("Estado de autenticación6:", autenticado);
            if (autenticado) {
                sessionStorage.setItem("btnAgendar", true);
                //ejecutamos la función pagar() en python
                //fetch('/pagar');


                //window.location.href = `agendar?ac=1&${parametros}`;
                window.location.href = '/api/pagar';
            } else {
                window.location.href = 'login?redirect=agendar&${parametros}';
            }
        });*/
    }
});


function guardarCamposNuevaMascotaEnSesion() {
    const campos = ['nombre_mascota', 'fecha_nacimiento', 'sexo_mascota', 'peso_mascota', 'especie_mascota', 'raza_mascota'];
    campos.forEach(campo => {
        const el = document.getElementById(campo);
        if (el && el.value) {
            fetch('/api/sesion/nueva_mascota', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ campo: campo, valor: el.value })
            });
        }
    });
}
