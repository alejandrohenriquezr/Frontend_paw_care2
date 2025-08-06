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

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const latUsuario = parseFloat(position.coords.latitude);
                    sessionStorage.setItem("latUsuario", latUsuario);

                    const lonUsuario = parseFloat(position.coords.longitude);
                    sessionStorage.setItem("lonUsuario", lonUsuario);

                    console.log("Latitud:", latUsuario, "Longitud:", lonUsuario);

                    let ordenadas = [...clinicasCercanas];

                    // Quitar clase 'activo' a todos los botones
                    document.querySelectorAll(".ordenador-btn").forEach(b => b.classList.remove("activo"));
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
                },
                function (error) {
                    console.error("Error obteniendo geolocalización:", error);
                    alert("No se pudo obtener tu ubicación.");
                }
            );
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

                    <form class="search-form mt-2" action="/" method="GET">
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

