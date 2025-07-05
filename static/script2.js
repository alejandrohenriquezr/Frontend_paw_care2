document.addEventListener("DOMContentLoaded", function () {





    
    const resultadosContainer = document.getElementById("resultados");
     const searchInput = document.getElementById("search-input");
     const suggestionsContainer = document.getElementById("suggestions");
    // 🔥 Capturar los parámetros de la URL al cargar la página
    const params = new URLSearchParams(window.location.search);
    const comunaParam = params.get("comuna");
    const searchParam = params.get("search");
    if (comunaParam) sessionStorage.setItem("comuna", comunaParam);
    if (searchParam) sessionStorage.setItem("busqueda", searchParam);

    // Obtener valores desde sessionStorage
    const comuna = sessionStorage.getItem("comuna") || "";
    const search = sessionStorage.getItem("busqueda") || "";
    console.log("Comuna desde sessionStorage:", comuna);
    console.log("Búsqueda desde sessionStorage:", search);

    // Al hacer foco (mostrar especialidades por omisión)
    searchInput.addEventListener("focus", async () => {
        console.log("Entrando al focus");

        const data = await fetchSugerencias("");
        console.log("la data en focus es:");
        console.log(data);
        suggestionsContainer.innerHTML = "";
        if (data.length > 0) {
            suggestionsContainer.style.display = "block";
            data.forEach(sugerencia => {
                const div = document.createElement("div");
                div.classList.add("suggestion-item");
                div.style.textAlign = "left";
                div.innerHTML = `<i class="fa fa-graduation-cap text-green-600 mr-2"></i> ${sugerencia}`;

                div.onclick = function() {
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
    
        async function obtenerNombreComuna(idDpa) {
        try {
            console.log("Obteniendo nombre de comuna para ID DPA:", idDpa);
            const response = await fetch(`/api/obtener_comuna/${idDpa}`);
            const data = await response.json();
            return data.nombre_comuna || "Comuna desconocida";
        } catch (error) {
            console.error("Error al obtener nombre de comuna:", error);
            return "Comuna desconocida";
        }
    }

    async function fetchSugerencias(query) {
        const comuna = document.getElementById("comunas")?.value || "";
        console.log("Comuna en fetchSugerencias:", comuna);
        console.log("query en fetchSugerencias:", query);
        const res = await fetch(`/sugerencias?q=${encodeURIComponent(query)}&comuna=${comuna}`);
        console.log("Respuesta del servidor:", res);
        return await res.json();
        //return;
    }
   
    let paginaActual = 1;
    const elementosPorPagina = 2;
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
            fila1.style.display = "flex";
            fila1.style.alignItems = "flex-start";  // Alineación vertical arriba
            fila1.classList.add("fila1");
            //const imagen = document.createElement("img");
            //imagen.src = `/static/images/id_${clinica.id_clinica}.jpg`;
            const imagen = new Image();
            const ruta = `/static/images/id_${clinica.id_clinica}.jpg`;
            const rutaGenerica = "/static/images/foto_generica_clinica.jpg";

            imagen.src = ruta;
            imagen.alt = clinica.nombre;
            imagen.width = 275;
            imagen.height = 184;

            // Verificar si la imagen real existe
            fetch(ruta, { method: "HEAD" })
            .then((res) => {
                if (!res.ok) {
                imagen.src = rutaGenerica;  // Reemplaza por la imagen real si existe
                }
            })
            .catch(() => {
                // Nada, ya está puesta la genérica
            });

            fila1.appendChild(imagen);


            const fila2 = document.createElement("div");
            fila2.classList.add("fila2");
            fila2.classList.add("fila2");
            fila2.style.display = "flex";
            fila2.style.alignItems = "flex-start";  // Alineación vertical arriba
            fila2.classList.add("fila2");            
            //fila1.className=`<h3 class="text-xl mb-2 text-[#333333]">`;
            
            fila2.textContent = clinica.nombre;

            const fila3 = document.createElement("div");
            fila3.classList.add("fila2");
            fila3.textContent =clinica.direccion;

            const fila4 = document.createElement("div");
            fila4.classList.add("fila2");
            fila4.textContent = `Comuna: ${clinica.dpa}`;

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

            const fila6 = document.createElement("div");
            fila6.classList.add("fila2");

            fila6.innerHTML += ` (${clinica.n_calificaciones} reseñas)`;

            // Formulario de agendar
            const fila7 = document.createElement("div");
            fila7.classList.add("fila2");

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
            botonSubmit.textContent = "Agendar cita";

            formulario.append(inputIdClinica, inputAccion, botonSubmit);
            fila6.appendChild(formulario);

            columna1.append(fila1, fila2, fila3, fila4, fila5, fila6, fila7);
            // Reemplazar luego con el nombre real
            obtenerNombreComuna(clinica.dpa).then(nombreComuna => {
                fila4.textContent = `Comuna: ${nombreComuna}`;
            });
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
            // Agregar una línea visual
        const linea = document.createElement("hr");
        linea.classList.add("my-4", "border-t", "border-gray-300");
        paginadorContainer.appendChild(linea);
    }



let paginadorContainer = document.getElementById("paginador");

async function obtenerIdDPA(nombreComuna) {
    const res = await fetch(`/api/obtener_dpa?nombre_comuna=${encodeURIComponent(nombreComuna)}`);
    const data = await res.json();
    return data.id_dpa || null;
}

async function cargarClinicas(comuna, search) {
    let comunaParam = comuna;

    if (/^[a-zA-Z\s]+$/.test(comuna)) {  // solo letras (nombre comuna)
        comunaParam = await obtenerIdDPA(comuna);
        if (!comunaParam) {
            console.error("No se pudo obtener ID DPA para la comuna");
            return;
        }
    }

    fetch(`/api/clinicas?comuna=${encodeURIComponent(comunaParam)}&search=${encodeURIComponent(search)}`)
        .then(response => response.json())
        .then(data => {
            clinicasData = data.clinicas || [];
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
        })
        .catch(error => console.error("Error cargando clínicas:", error));
}
cargarClinicas(comuna, search);

});

document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  const params = new URLSearchParams(window.location.search);
  const searchParam = params.get("search");

  if (searchInput) {
    if (searchParam && searchParam.trim() !== "") {
      searchInput.placeholder = searchParam;
    } else {
      searchInput.placeholder = "Especialidad, clínica o veterinario";
    }
  }



});


