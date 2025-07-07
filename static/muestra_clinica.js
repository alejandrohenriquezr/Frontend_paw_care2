document.addEventListener("DOMContentLoaded", function () {
    const resultadosContainer = document.getElementById("datos_de_la_clinica");


    resultadosContainer.classList.add("contenedor-grid");

    // 🔥 Obtener id_clinica de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const parametros = urlParams.get("params") || "";

    let id_clinica = urlParams.get("id_clinica");
    if (!id_clinica) {
        id_clinica = sessionStorage.getItem("id_clinica");
    }

    // 🔥 Llamar a la API para obtener todas las clínicas
    fetch("/api/clinicas")  
    .then(response => response.json())
    .then(data => {
        const clinica = data.clinicas.find(c => c.id_clinica == id_clinica);
        
        if (!clinica) {
            resultadosContainer.innerHTML = "<p>⚠ No se encontró la clínica.</p>";
            return;
        }

        const latUsuario = parseFloat(sessionStorage.getItem("lat_usuario"));
        const lonUsuario = parseFloat(sessionStorage.getItem("lon_usuario"));

        // 🔥 Contenedor principal con estilo flex
        const contenedor = document.createElement("div");
        contenedor.classList.add("flex", "container", "px-4", "mx-auto");

        // 🔥 Columna 1: Imagen + información
        const columna1 = document.createElement("div");
        columna1.classList.add("w-full", "md:w-1/4");

        const imagen = document.createElement("img");
        imagen.src = `/static/images/id_${clinica.id_clinica}.jpg`;
        imagen.alt = clinica.nombre;
        imagen.width = 275;
        imagen.height = 184;
        imagen.classList.add("rounded", "mb-4");
        imagen.onerror = function() {
            this.onerror = null;
            this.src = '/static/images/foto_generica_clinica.jpg';
        };

        const fila1 = document.createElement("div");
        fila1.classList.add("text-lg", "font-bold", "mb-2");
        fila1.innerHTML = `${clinica.nombre}`;

        const fila2 = document.createElement("div");
        fila2.classList.add("mb-1");
        fila2.textContent = clinica.direccion;

        const fila3 = document.createElement("div");
        fila3.classList.add("mb-1");
        fila3.textContent = `Comuna: ${clinica.Nombre_Comuna || "Desconocida"}`;

        const fila4 = document.createElement("div");
        fila4.classList.add("estrellas-container", "mb-2");

        const calificacion = parseFloat(clinica.calificacion.replace(",", "."));
        const parteEntera = Math.floor(calificacion);
        const parteDecimal = calificacion - parteEntera;

        fila4.innerHTML = `${clinica.calificacion} `;
        for (let i = 0; i < parteEntera; i++) {
            fila4.innerHTML += `<img src="/static/icons/star.png" width="15"> `;
        }
        if (parteDecimal > 0.1) {
            fila4.innerHTML += `<img src="/static/icons/star_2.png" width="15"> `;
        }
        fila4.innerHTML += ` (${clinica.n_calificaciones} reseñas)`;

        columna1.append(imagen, fila1, fila2, fila3, fila4);

        // 🔥 Columna 2: Mapa
        const columna2 = document.createElement("div");
        columna2.classList.add("w-full", "md:w-3/4");

        const mapaDiv = document.createElement("div");
        mapaDiv.id = `mapa_clinica`;
        mapaDiv.style.height = "100%";
        mapaDiv.style.width = "100%";
        mapaDiv.classList.add("rounded-lg", "border", "border-gray-300");

        columna2.appendChild(mapaDiv);

        // 🔥 Agregar columnas al contenedor principal
        contenedor.append(columna1, columna2);

        // 🔥 Agregar el contenedor al DOM antes de crear el mapa
        resultadosContainer.appendChild(contenedor);

        // 🔥 Crear el mapa después del renderizado
        setTimeout(() => {
            if (typeof L === 'undefined') {
                console.error("Leaflet no está cargado");
                return;
            }

            console.log("Mapa creado para la clínica:", clinica.nombre);
            console.log("Latitud:", clinica.latitud, "Longitud:", clinica.longitud);

            const map = L.map("mapa_clinica").setView([parseFloat(clinica.latitud.replace(",", ".")), parseFloat(clinica.longitud.replace(",", "."))], 14);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors"
            }).addTo(map);

            L.marker([parseFloat(clinica.latitud.replace(",", ".")), parseFloat(clinica.longitud.replace(",", "."))])
                .addTo(map)
                .bindPopup(clinica.nombre)
                .openPopup();
            const latUsuario = parseFloat(sessionStorage.getItem("lat_usuario"));
            const lonUsuario = parseFloat(sessionStorage.getItem("lon_usuario"));
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
                .bindPopup("Tu ubicación");
            }
        }, 0);        
    })
    .catch(error => console.error("Error cargando clínicas:", error));

});




