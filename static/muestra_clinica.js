document.addEventListener("DOMContentLoaded", function () {
    const resultadosContainer = document.getElementById("datos_de_la_clinica");
    resultadosContainer.classList.add("contenedor-grid");

    // 🔥 Obtener id_clinica de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const parametros = urlParams.get("params") || "";

    id_clinica = urlParams.get("id_clinica");
    if (!id_clinica) {

        id_clinica = sessionStorage.getItem("id_clinica");
        //const id_clinica = parametros.split("=")[1];
        //console.log("id_clinicaxxxxx=", parametros.split("=")[1]);
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

            // 🔥 Crear el contenedor de la clínica
            const contenedor = document.createElement("div");
//            contenedor.classList.add("contenedor");

            // 🔥 Columna 1: Imagen de la clínica
            const columna1 = document.createElement("div");
            columna1.classList.add("columna-1");

            const imagen = document.createElement("img");
            imagen.src = `/static/images/id_${clinica.id_clinica}.jpg`;
            imagen.alt = clinica.nombre;
            imagen.width = 275;
            imagen.height = 184;
            imagen.onerror = function() {
                this.onerror = null;
                this.src = '/static/images/foto_generica_clinica.jpg';
            };

            columna1.appendChild(imagen);

            // 🔥 Columna 2: Información de la clínica
            const columna2 = document.createElement("div");
            columna2.classList.add("columna-2");

            const fila1 = document.createElement("div");
            fila1.classList.add("fila2");
            fila1.innerHTML = `<strong>${clinica.nombre}</strong>`;

            const fila2 = document.createElement("div");
            fila2.classList.add("fila2");
            fila2.textContent = clinica.direccion;

            const fila3 = document.createElement("div");
            fila3.classList.add("fila2");
            fila3.textContent = `DPA: ${clinica.dpa}`;

            const fila4 = document.createElement("div");
            fila4.classList.add("fila2", "estrellas-container");

            const calificacion = parseFloat(clinica.calificacion.replace(",", "."));
            const parteEntera = Math.floor(calificacion);
            const parteDecimal = calificacion - parteEntera;

            fila4.innerHTML = `${clinica.calificacion} `;

            // 🔥 Agregar estrellas
            for (let i = 0; i < parteEntera; i++) {
                fila4.innerHTML += `<img src="/static/icons/star.png" width="15"> `;
            }
            if (parteDecimal > 0.1) {
                fila4.innerHTML += `<img src="/static/icons/star_2.png" width="15"> `;
            }
            fila4.innerHTML += ` (${clinica.n_calificaciones} reseñas)`;

            // 🔥 Agregar todo al contenedor principal
            columna2.append(fila1, fila2, fila3, fila4);
            contenedor.append(columna1, columna2);
            resultadosContainer.appendChild(contenedor);
        })
        .catch(error => console.error("Error cargando clínicas:", error));
});



