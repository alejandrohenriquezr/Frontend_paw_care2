document.addEventListener("DOMContentLoaded", function () {
    const resultadosContainer = document.getElementById("resultados");
    const searchInput = document.getElementById("search-input");
    const suggestionsContainer = document.getElementById("suggestions");
    const paginadorContainer = document.getElementById("paginador");

    const params = new URLSearchParams(window.location.search);
    const comunaParam = params.get("comuna");
    const searchParam = params.get("search");

    if (comunaParam) sessionStorage.setItem("comuna", comunaParam);
    if (searchParam) sessionStorage.setItem("busqueda", searchParam);

    const comuna = sessionStorage.getItem("comuna") || "";
    const search = sessionStorage.getItem("busqueda") || "";

    if (searchInput) {
        searchInput.placeholder = searchParam && searchParam.trim() !== ""
            ? searchParam
            : "Especialidad, clínica o veterinario";
    }

    searchInput.addEventListener("focus", async () => {
        const data = await fetchSugerencias("");
        suggestionsContainer.innerHTML = "";
        if (data.length > 0) {
            suggestionsContainer.style.display = "block";
            data.forEach(sugerencia => {
                const div = document.createElement("div");
                div.classList.add("suggestion-item");
                div.innerHTML = `<i class="fa fa-graduation-cap text-green-600 mr-2"></i> ${sugerencia}`;
                div.onclick = () => {
                    searchInput.value = sugerencia;
                    suggestionsContainer.innerHTML = "";
                    suggestionsContainer.style.display = "none";
                };
                suggestionsContainer.appendChild(div);
            });
        } else {
            suggestionsContainer.style.display = "none";
        }
    });

    async function fetchSugerencias(query) {
        const comuna = document.getElementById("comunas")?.value || "";
        const res = await fetch(`/sugerencias?q=${encodeURIComponent(query)}&comuna=${comuna}`);
        return await res.json();
    }

    async function obtenerNombreComuna(idDpa) {
        try {
            const response = await fetch(`/api/obtener_comuna/${idDpa}`);
            const data = await response.json();
            return data.nombre_comuna || "Comuna desconocida";
        } catch {
            return "Comuna desconocida";
        }
    }

    let paginaActual = 1;
    const elementosPorPagina = 2;
    let clinicasData = [];

    function mostrarPagina(pagina) {
        resultadosContainer.innerHTML = "";
        const inicio = (pagina - 1) * elementosPorPagina;
        const fin = inicio + elementosPorPagina;
        const clinicasPagina = clinicasData.slice(inicio, fin);
        //const latUsuario = (position.coords.latitude);
        //const lonUsuario = (position.coords.longitude);
        //console.log(`Mostrando latUsuario en mostrarPagina ${latUsuario} lonUsuario ${lonUsuario} en la página ${pagina}`);

        clinicasPagina.forEach(clinica => {
            const contenedor = document.createElement("div");
            contenedor.classList.add("contenedor");

            const columna1 = document.createElement("div");
            columna1.classList.add("columna-1");

            const fila1 = document.createElement("div");
            fila1.classList.add("fila1");
            const imagen = new Image();
            const ruta = `/static/images/id_${clinica.id_clinica}.jpg`;
            const rutaGenerica = "/static/images/foto_generica_clinica.jpg";
            imagen.src = ruta;
            imagen.alt = clinica.nombre;
            imagen.width = 275;
            imagen.height = 184;
            fetch(ruta, { method: "HEAD" }).then(res => {
                if (!res.ok) imagen.src = rutaGenerica;
            });
            fila1.appendChild(imagen);

            const fila2 = document.createElement("div");
            fila2.classList.add("fila2");
            console.log("staffData", staffData);
            fila2.innerHTML = clinica.nombre;

            for (let i = 1; i < staffData.length; i++) {
                if (staffData[i]?.id_clinica == clinica.id_clinica) {
                    fila2.innerHTML += "<br>Vet. " + staffData[i]?.nombre_completo;
                }
            }

            

            const fila3 = document.createElement("div");
            fila3.classList.add("fila2");
            fila3.textContent = "Dir. " + clinica.direccion;

            const fila4 = document.createElement("div");
            fila4.classList.add("fila2");
            obtenerNombreComuna(clinica.dpa).then(nombreComuna => {
                fila4.textContent = `${nombreComuna}`;
            });

            const fila5 = document.createElement("div");
            fila5.classList.add("fila2", "estrellas-container");
            const calificacion = parseFloat(clinica.calificacion.replace(",", "."));
            const parteEntera = Math.floor(calificacion);
            const parteDecimal = calificacion - parteEntera;
            //fila5.innerHTML = `${clinica.calificacion} `;
            for (let i = 0; i < parteEntera; i++) fila5.innerHTML += `<img src="/static/icons/star.png" width="15"> `;
            if (parteDecimal > 0.1) fila5.innerHTML += `<img src="/static/icons/star_2.png" width="15"> `;

            const fila6 = document.createElement("div");
            fila6.classList.add("fila2");
            fila6.innerHTML = `(${clinica.n_calificaciones} reseñas)`;

            const fila7 = document.createElement("div");
            fila7.classList.add("fila2");
            //alinear el contenido al centro
            fila7.style.textAlign = "center";
            fila7.style.marginTop = "10px";
            const formulario = document.createElement("form");
            formulario.classList.add("search-form");
            formulario.action = "/agendar";
            formulario.method = "GET";
            formulario.innerHTML = `
                <input type="hidden" name="id_clinica" value="${clinica.id_clinica}">
                <input type="hidden" name="accion_agendar" value="1">
                <button type="submit" class="w-full py-2 bg-[#5A8F99] text-white rounded-lg border-2 border-[#5A8F99] shadow-lg hover:bg-[#4F7F88] transition duration-200">Agendar cita</button>

            `;
            //"mt-2 px-4 py-2 bg-[#2563eb] text-white rounded-lg border-2 border-indigo-600 shadow-lg hover:bg-indigo-700 transition duration-200"
            fila7.innerHTML = `
                <!-- Botón Waze -->
                <button onclick="window.open('https://waze.com/ul?ll=${clinica.latitud},${clinica.longitud}&navigate=yes&z=10', '_blank')"
                    class="w-full h-10 mt-4 flex items-center justify-center gap-3 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition px-4">
                    <!--<img src="/static/images/logo_waze.png" alt="Waze" width="32" height="32" class="inline-block align-middle"> -->
                    ¿Cómo llegar con Waze?</span>
                </button>

                <!-- Botón Google Maps -->
                <button onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${clinica.latitud},${clinica.longitud}', '_blank')"
                    class="w-full h-10 mt-4 flex items-center justify-center gap-3 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 transition px-4">
                    <!--<img src="/static/images/google_maps_icon.png" alt="Google Maps" width="32" height="32" class="inline-block align-middle"> -->
                    ¿Cómo llegar con Google Maps?</span>
                </button><br>
            `;

            fila7.appendChild(formulario);


            columna1.append(fila1, fila2, fila3, fila4, fila5, fila6, fila7);
            contenedor.appendChild(columna1);
            resultadosContainer.appendChild(contenedor);
        });

        actualizarPaginador();
    }

    function actualizarPaginador() {
        paginadorContainer.innerHTML = "";
        const totalPaginas = Math.ceil(clinicasData.length / elementosPorPagina);
        for (let i = 1; i <= totalPaginas; i++) {
            const botonPagina = document.createElement("button");
            botonPagina.textContent = i;
            botonPagina.classList.add("paginador-boton");
            if (i === paginaActual) botonPagina.classList.add("activo");
            botonPagina.addEventListener("click", () => {
                paginaActual = i;
                mostrarPagina(paginaActual);
            });
            paginadorContainer.appendChild(botonPagina);
        }
        const linea = document.createElement("hr");
        linea.classList.add("my-4", "border-t", "border-gray-300");
        paginadorContainer.appendChild(linea);
    }

    async function obtenerIdDPA(nombreComuna) {
        const res = await fetch(`/api/obtener_dpa?nombre_comuna=${encodeURIComponent(nombreComuna)}`);
        const data = await res.json();
        return data.id_dpa || null;
    }

    async function cargarClinicas(comuna, search) {
        let comunaParam = comuna;
        if (/^[a-zA-Z\s]+$/.test(comuna)) {
            comunaParam = await obtenerIdDPA(comuna);
            if (!comunaParam) return;
        }
        const response = await fetch(`/api/clinicas?comuna=${encodeURIComponent(comunaParam)}&search=${encodeURIComponent(search)}`);
        const data = await response.json();
        clinicasData = data.clinicas || [];
        staffData = data.staff_json || [];
        if (clinicasData.length === 0) {
            sessionStorage.removeItem("busqueda");
            sessionStorage.removeItem("comuna");
            resultadosContainer.innerHTML = `
                <div class='w-full flex justify-center items-center py-8'>
                    <p class='text-gray-600 text-center text-lg'>No se encontraron clínicas.</p>
                </div>`;
            return;
        }
        mostrarPagina(1);
    }

    cargarClinicas(comuna, search);
    let clinicasCercanas = [];
    let paginaActualRecomendadas = 1;
    const ClinicasCercanasPorPagina = 4;

    async function mostrarClinicasCercanasDesdeStorage() {
        const lat = parseFloat(sessionStorage.getItem("lat_usuario"));
        const lon = parseFloat(sessionStorage.getItem("lon_usuario"));

        if (!lat || !lon) {
            console.warn("Ubicación del usuario no disponible aún.");
            return;
        }

        try {
            const res = await fetch(`/api/clinicas_cercanas?lat=${lat}&lon=${lon}`);
            clinicasCercanas = await res.json();

            paginaActualRecomendadas = 1;
            mostrarPaginaRecomendadas(paginaActualRecomendadas, lat, lon);
        } catch (error) {
            console.error("Error mostrando clínicas cercanas:", error);
        }
    }

    document.querySelectorAll(".ordenador-btn").forEach(btn => {
        btn.onclick = () => {
            const criterio = btn.dataset.sort;
            const latUsuario = parseFloat(sessionStorage.getItem("lat_usuario"));
            const lonUsuario = parseFloat(sessionStorage.getItem("lon_usuario"));

            let ordenadas = [...clinicasCercanas]; // Copia segura para no modificar el original por referencia
            // Quitar clase 'activo' a todos los botones
            document.querySelectorAll(".ordenador-btn").forEach(b => b.classList.remove("activo"));

            // Agregar clase 'activo' al botón clickeado
            btn.classList.add("activo");
            switch (criterio) {
                case "distancia_asc":
                    ordenadas.sort((a, b) => a.distancia - b.distancia);
                    break;
                case "distancia_desc":
                    ordenadas.sort((a, b) => b.distancia - a.distancia);
                    break;
                case "calificacion_asc":
                    ordenadas.sort((a, b) =>
                        parseFloat(a.calificacion.replace(",", ".")) -
                        parseFloat(b.calificacion.replace(",", "."))
                    );
                    break;
                case "calificacion_desc":
                    ordenadas.sort((a, b) =>
                        parseFloat(b.calificacion.replace(",", ".")) -
                        parseFloat(a.calificacion.replace(",", "."))
                    );
                    break;                    
                case "resenas_asc":
                    ordenadas.sort((a, b) =>
                        parseInt(a.n_calificaciones) - parseInt(b.n_calificaciones)
                    );
                    break;
                case "resenas_desc":
                    ordenadas.sort((a, b) =>
                        parseInt(b.n_calificaciones) - parseInt(a.n_calificaciones)
                    );
                    break;
            }

            clinicasCercanas = ordenadas;
            paginaActualRecomendadas = 1;
            mostrarPaginaRecomendadas(paginaActualRecomendadas, latUsuario, lonUsuario);
        };
    });


    function mostrarPaginaRecomendadas(pagina, latUsuario, lonUsuario) {
        console.log(`Mostrando latUsuario ${latUsuario} lonUsuario ${lonUsuario} en la página ${pagina}`);

        const contenedor = document.getElementById("clinicas_recomendadas");
        contenedor.innerHTML = "";

        const inicio = (pagina - 1) * ClinicasCercanasPorPagina;
        const fin = inicio + ClinicasCercanasPorPagina;
        const clinicasPagina = clinicasCercanas.slice(inicio, fin);


        
        clinicasPagina.forEach((c, index) => {
            const div = document.createElement("div");
            div.className = "bg-white p-4 rounded-lg shadow-lg flex flex-col md:flex-row gap-4";

            const calificacion = parseFloat(c.calificacion.replace(",", "."));
            const parteEntera = Math.floor(calificacion);
            const parteDecimal = calificacion - parteEntera;
            let estrellasHTML = `(${c.calificacion}) `;
            for (let i = 0; i < parteEntera; i++) estrellasHTML += `<img src="/static/icons/star.png" width="15"> `;
            if (parteDecimal > 0.1) estrellasHTML += `<img src="/static/icons/star_2.png" width="15"> `;

            div.innerHTML = `
                <div class="flex-1">
                    <h3 class="text-lg font-bold text-[#2E2E2E]">${c.nombre}</h3>
                    <p class="text-sm text-gray-800">${c.direccion} (${(c.distancia).toFixed(1)}Km.)</p>
                    <p class="text-sm text-gray-700">Comuna: ${c.Nombre_Comuna}</p>
                    <div class="flex items-center justify-center space-x-1 mt-1 text-sm text-gray-700">${estrellasHTML}</div>
                    <p class="text-sm text-gray-700">Reseñas: ${c.n_calificaciones}</p>

                    <button onclick="window.open('https://waze.com/ul?ll=${c.latitud},${c.longitud}&navigate=yes&z=10', '_blank')" 
                            class="mt-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition">
                       ¿Cómo llegar con Waze?
                    </button>
                    <button onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${c.latitud},${c.longitud}&origin=${latUsuario},${lonUsuario}', '_blank')" 
                            class="mt-2 px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition">
                        ¿Cómo llegar con Google Maps?
                    </button>

                    <form class="search-form mt-2" action="/agendar" method="GET">
                        <input type="hidden" name="id_clinica" value="${c.id_clinica}">
                        <input type="hidden" name="accion_agendar" value="1">
                        <button type="submit" class="w-full py-2 bg-[#5A8F99] text-white rounded-lg border-2 border-[#5A8F99] shadow-lg hover:bg-[#4F7F88] transition duration-200">
                            Agendar cita
                        </button>
                    </form>

                    <img src="/static/images/id_${c.id_clinica}.jpg" 
                    alt="${c.nombre}" 
                    class="w-full h-48 object-contain rounded-lg mt-2"
                    onerror="this.onerror=null; this.src='/static/images/foto_generica_clinica.jpg';">
                </div>
                <div id="map${index}" class="w-full md:w-2/3 h-80 rounded-lg border border-gray-300"></div>
            `;

            contenedor.appendChild(div);

            setTimeout(() => {
                const map = L.map(`map${index}`).setView([c.latitud, c.longitud], 14);
                L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                    attribution: "© OpenStreetMap contributors"
                }).addTo(map);

                L.marker([c.latitud, c.longitud]).addTo(map).bindPopup(c.nombre).openPopup();

                if (!isNaN(latUsuario) && !isNaN(lonUsuario)) {
                    L.marker([latUsuario, lonUsuario], {
                        icon: L.icon({
                            iconUrl: "/static/images/ubicacion.png",
                            iconSize: [41, 41],
                            iconAnchor: [12, 41],
                            popupAnchor: [0, -41]
                        })
                    })
                    .addTo(map)
                    .bindPopup("Tu ubicación")
                    
                }
            }, 0);
        });

        actualizarPaginadorRecomendadas(latUsuario, lonUsuario);
    }

    function actualizarPaginadorRecomendadas(latUsuario, lonUsuario) {
        const paginador = document.getElementById("paginador_recomendadas");
        if (!paginador) return;

        paginador.innerHTML = "";
        const totalPaginas = Math.ceil(clinicasCercanas.length / elementosPorPagina);

        for (let i = 1; i <= totalPaginas; i++) {
            const btn = document.createElement("button");
            btn.textContent = i;
            btn.className = "mx-1 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300";
            if (i === paginaActualRecomendadas) {
                btn.classList.add("bg-blue-500", "text-white");
            }
            btn.onclick = () => {
                paginaActualRecomendadas = i;
                mostrarPaginaRecomendadas(i, latUsuario, lonUsuario);
            };
            paginador.appendChild(btn);
        }
    }

    mostrarClinicasCercanasDesdeStorage();


});

