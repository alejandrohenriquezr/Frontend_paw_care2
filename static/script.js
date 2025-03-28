document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("search-form");
    const searchInput = document.getElementById("search-input");
    //const resultadosContainer = document.getElementById("resultados");
    const agendar_resultadosContainer = document.getElementById("agendar_resultados");

    form.addEventListener("submit", async function(event) {
        event.preventDefault(); // Evitar que el formulario de búsqueda recargue la página
        console.log("Formulario enviado!");
        const query = searchInput.value.trim();
        if (query.length === 0) return;

        try {
            const response = await fetch("/buscar_clinicas", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            resultadosContainer.innerHTML = ""; // Limpiar resultados anteriores

            if (data.clinicas.length > 0) {
                data.clinicas.forEach(clinica => {
                    const contenedor = document.createElement("div");
                    contenedor.classList.add("contenedor");

                    // Imagen de la clínica
                    const columna1 = document.createElement("div");
                    columna1.classList.add("columna-1");
                    const imagen = document.createElement("img");
                    imagen.src = `/static/images/id_${clinica.id_clinica}.jpg`;
                    imagen.alt = clinica.nombre;
                    imagen.width = 275;
                    imagen.height = 184;
                    columna1.appendChild(imagen);

                    // Columna 2 con la información
                    const columna2 = document.createElement("div");
                    columna2.classList.add("columna-2");

                    const fila1 = document.createElement("div");
                    fila1.classList.add("fila");
                    fila1.innerHTML = `<strong>${clinica.nombre}</strong>`;

                    const fila2 = document.createElement("div");
                    fila2.classList.add("fila");
                    fila2.textContent = clinica.direccion;

                    const fila3 = document.createElement("div");
                    fila3.classList.add("fila");
                    fila3.textContent = `DPA: ${data.dpa}`;

                    const fila4 = document.createElement("div");
                    fila4.classList.add("fila");
                    const calificacion1 = (clinica.calificacion.replace(",", "."));
                    const calificacion = parseFloat(calificacion1);
                    const parteEntera = Math.floor(calificacion);
                    const parteDecimal = calificacion - parteEntera;

                    fila4.innerHTML = `${clinica.calificacion} `;

                    // Agregar estrellas completas
                    for (let i = 0; i < parteEntera; i++) {
                        fila4.innerHTML += `<img src="/static/icons/star.png" width="15"> `;
                    }

                    // Agregar media estrella si la parte decimal es mayor a 0.1
                    if (parteDecimal > 0.1) {
                        fila4.innerHTML += `<img src="/static/icons/star_2.png" width="15"> `;
                    }

                    fila4.innerHTML += ` (${clinica.n_calificaciones})`;

                    // 🔥 Agregar una fila con un formulario válido
                    const fila5 = document.createElement("div");
                    fila5.classList.add("fila");

                    const formulario = document.createElement("form");
                    formulario.id_clinica = `search-form_${clinica.id_clinica}`;
                    formulario.classList.add("search-form");
                    formulario.action = "agendar.html";
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
                    botonSubmit.textContent = "Agendar citas";  // 🔥 Botón corregido

                    formulario.append(inputIdClinica, inputAccion, botonSubmit);
                    fila5.appendChild(formulario);

                    columna2.append(fila1, fila2, fila3, fila4, fila5);
                    contenedor.append(columna1, columna2);
                    resultadosContainer.appendChild(contenedor);
                });
            } else {
                resultadosContainer.innerHTML = "<p>No se encontraron coincidencias.</p>";
            }
        } catch (error) {
            console.error("Error en la búsqueda:", error);
        }
    });

    // 🔥 Solución para permitir el submit en formularios de "Agendar cita"
    document.addEventListener("submit", function(event) {
        if (event.target.classList.contains("search-form") && event.target.action.includes("agendar.html")) {
            return;  // Permitir el envío del formulario
        }
        event.preventDefault();  // Bloquear solo el formulario de búsqueda
    });
});
