document.addEventListener("DOMContentLoaded", function () {
    const resultadosContainer = document.getElementById("resultados");
    resultadosContainer.classList.add("contenedor-grid");

    let paginaActual = 1;
    const elementosPorPagina = 3;
    let clinicasData = [];

    function mostrarPagina(pagina) {
        resultadosContainer.innerHTML = "";
        const inicio = (pagina - 1) * elementosPorPagina;
        const fin = inicio + elementosPorPagina;
        const clinicasPagina = clinicasData.slice(inicio, fin);

        clinicasPagina.forEach(clinica => {
            const contenedor = document.createElement("div");
            contenedor.classList.add("contenedor");

            // Imagen de la clínica
            const columna1 = document.createElement("div");
            columna1.classList.add("columna-1");
            const fila1 = document.createElement("div");
            fila1.classList.add("fila1");
            const imagen = document.createElement("img");
            imagen.src = `/static/images/id_${clinica.id_clinica}.jpg`;
            imagen.alt = clinica.nombre;
            imagen.width = 275;
            imagen.height = 184;
            
            fila1.appendChild(imagen);

            const fila2 = document.createElement("div");
            fila2.classList.add("fila2");
            //fila1.className=`<h3 class="text-xl mb-2 text-[#333333]">`;
            
            fila2.textContent = clinica.nombre;

            const fila3 = document.createElement("div");
            fila3.classList.add("fila2");
            fila3.textContent =clinica.direccion;

            const fila4 = document.createElement("div");
            fila4.classList.add("fila2");
            fila4.textContent = `DPA: ${clinica.dpa}`;

            const fila5 = document.createElement("div");
            fila5.classList.add("fila2", "estrellas-container");
            const calificacion = parseFloat(clinica.calificacion.replace(",", "."));
            const parteEntera = Math.floor(calificacion);
            const parteDecimal = calificacion - parteEntera;

            fila5.innerHTML = `${clinica.calificacion} `;
            for (let i = 0; i < parteEntera; i++) {
                fila5.innerHTML += `<img src="/static/icons/star.png" width="15"> `;
            }
            if (parteDecimal > 0.1) {
                fila5.innerHTML += `<img src="/static/icons/star_2.png" width="15"> `;
            }
            fila5.innerHTML += ` (${clinica.n_calificaciones} reseñas)`;

            // Formulario de agendar
            const fila6 = document.createElement("div");
            fila6.classList.add("fila2");

            const formulario = document.createElement("form");
            formulario.classList.add("search-form");
            formulario.action = "/agendar";
            formulario.method = "GET";

            const inputIdClinica = document.createElement("input");
            inputIdClinica.type = "hidden";
            inputIdClinica.name = "id_clinica";
            inputIdClinica.value = clinica.id_clinica;

            const inputAccion = document.createElement("input");
            inputAccion.type = "hidden";
            inputAccion.name = "accion_agendar";
            inputAccion.value = "1";

            const botonSubmit = document.createElement("button");
            botonSubmit.type = "submit";
            botonSubmit.className="w-full py-2 bg-[#5A8F99] text-white rounded-lg border-2 border-[#5A8F99] shadow-lg hover:bg-[#4F7F88] transition duration-200"
            botonSubmit.textContent = "Agendar citas";

            formulario.append(inputIdClinica, inputAccion, botonSubmit);
            fila6.appendChild(formulario);

            columna1.append(fila1, fila2, fila3, fila4, fila5, fila6);
            contenedor.append(columna1);
            resultadosContainer.appendChild(contenedor);
        });

        actualizarPaginador();
    }

    function actualizarPaginador() {
        const paginadorContainer = document.getElementById("paginador");
        paginadorContainer.innerHTML = "";

        const totalPaginas = Math.ceil(clinicasData.length / elementosPorPagina);
        for (let i = 1; i <= totalPaginas; i++) {
            const botonPagina = document.createElement("button");
            botonPagina.textContent = i;
            botonPagina.classList.add("paginador-boton");
            if (i === paginaActual) {
                botonPagina.classList.add("activo");
            }
            botonPagina.addEventListener("click", () => {
                paginaActual = i;
                mostrarPagina(paginaActual);
            });
            paginadorContainer.appendChild(botonPagina);
        }
    }

    fetch("/api/clinicas")  // Ajustar el endpoint según sea necesario
        .then(response => response.json())
        .then(data => {
            clinicasData = data.clinicas;
            mostrarPagina(1);
        })
        .catch(error => console.error("Error cargando clínicas:", error));
});


