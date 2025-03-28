document.addEventListener("DOMContentLoaded", function() {
    const resultadosContainer = document.getElementById("agendar_resultados");

    // Obtener el ID de la clínica de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const id_clinica = urlParams.get("id_clinica");

   // const urlParams = new URLSearchParams(window.location.search);
   // const idClinica = urlParams.get('id_clinica');
    //const accionAgendar = urlParams.get('accion_agendar');
    
    //const idClinica = document.getElementById("param_id_clinica").textContent.trim();
    if (!idClinica || idClinica === "No recibido") {
        resultadosContainer.innerHTML = "<p>Error: No se recibió información de la clínica.</p>";
        return;
    }

    // 🔥 Hacer una solicitud al servidor para obtener la clínica seleccionada
    fetch(`/api/clinica/${id_clinica}`)
        .then(response => response.json())
        .then(data => {
            console.log("Número de registros recibidos:", data[0].id_clinica);

            if (data.error) {
                resultadosContainer.innerHTML = `<p>${data.error}</p>`;
                return;
            }

            // 🔥 Construir el contenedor con los detalles de la clínica
            const contenedor = document.createElement("div");
            contenedor.classList.add("contenedor");

            // Columna 1: Imagen de la clínica
            const columna1 = document.createElement("div");
            columna1.classList.add("columna-1");

            const fila1_1 = document.createElement("div");

            const imagen = document.createElement("img");
            imagen.src = `/static/images/id_${data[0].id_clinica}.jpg`;
            imagen.alt = data[0].nombre;
            imagen.width = 275;
            imagen.height = 184;
            fila1_1.appendChild(imagen);

            const fila1 = document.createElement("div");
            fila1.classList.add("fila");
            fila1.innerHTML = `<strong>${data[0].nombre}</strong>`;

            const fila2 = document.createElement("div");
            fila2.classList.add("fila");
            fila2.textContent = data[0].direccion;

            const fila3 = document.createElement("div");
            fila3.classList.add("fila");
            fila3.textContent = `DPA: ${data[0].dpa}`;

            const fila4 = document.createElement("div");
            fila4.classList.add("fila");
            const primerRegistro = data[0];
            const calificacionStr = String(primerRegistro.calificacion).replace(",", ".");
            const calificacion = parseFloat(calificacionStr);
            //const calificacion1 = (data[0].calificacion.replace(",", "."));
            //const calificacion = parseFloat(calificacion1);
            const parteEntera = Math.floor(calificacion);
            const parteDecimal = calificacion - parteEntera;

            fila4.innerHTML = `${data[0].calificacion} `;
            
            // Agregar estrellas completas
            for (let i = 0; i < parteEntera; i++) {
                fila4.innerHTML += `<img src="/static/icons/star.png" width="15">`;
            }

            // Agregar media estrella si la parte decimal es mayor a 0.1
            if (parteDecimal > 0.1) {

                fila4.innerHTML += `<img src="/static/icons/star_2.png" width="15" height="15" font-size: 24px !important;> `;
                
            }
            fila4.innerHTML += ` (${data[0].n_calificaciones})`;


            columna1.append(fila1_1, fila1, fila2, fila3, fila4);

            // Columna 2: Información del staff
            const columna2 = document.createElement("div");
            columna2.classList.add("columna-2");
            
            //Crear filas para identificar medicos;
            const fila2_1 = document.createElement("div");
            fila2_1.classList.add("fila");
            const foto_vet = document.createElement("img");
            foto_vet.src = `/static/images/vet_${data[0].id_vet}.jpg`;
            foto_vet.alt = data[0].nombres;
            foto_vet.width = 150;
            foto_vet.height = 100;
            fila2_1.appendChild(foto_vet);

            const fila2_2 = document.createElement("div");
            fila2_2.classList.add("fila");            
            fila2_2.textContent = data[0].nombres + " " + data[0].apellidos;

            //const fila2_3 = document.createElement("div");
            //fila2_3.classList.add("fila");            
            //fila2_3.textContent = data[0].especialidad;

                       

            columna2.append(fila2_1, fila2_2);
            // 🔥 Generar dinámicamente los divs de especialidad
            data.forEach((registro, index) => {
                const filaEspecialidad = document.createElement("div");
                filaEspecialidad.classList.add("fila");
                filaEspecialidad.textContent = `Especialidad ${index + 1}: ${registro.especialidad}`;
                
                // Agregar cada especialidad a columna2
                columna2.appendChild(filaEspecialidad);

                const filaDescripcion = document.createElement("div");
                filaDescripcion.classList.add("fila");
                filaDescripcion.textContent = `${registro.descripcion}`;
                
                // Agregar cada especialidad a columna2
                columna2.appendChild(filaDescripcion);                
            });



            
            // 🔥 Crear formulario GET para "Ver calendario"
            const filaFormulario = document.createElement("div");
            filaFormulario.classList.add("fila");

            const formulario = document.createElement("form");
            formulario.method = "GET";
            formulario.action = "agendar.html";  // Redirige a la misma página

            // Campos ocultos
            const inputIdClinica = document.createElement("input");
            inputIdClinica.type = "hidden";
            inputIdClinica.name = "id_clinica";
            inputIdClinica.value = data[0].id_clinica;

            const inputAccion = document.createElement("input");
            inputAccion.type = "hidden";
            inputAccion.name = "accion_agendar";
            inputAccion.value = "1";

            const inputV = document.createElement("input");
            inputV.type = "hidden";
            inputV.name = "v";
            inputV.value = data[0].id_vet;

            // Botón submit
            const botonSubmit = document.createElement("button");
            botonSubmit.type = "submit";
            botonSubmit.textContent = "Ver calendario";

            // Agregar elementos al formulario
            formulario.append(inputIdClinica, inputAccion, inputV, botonSubmit);
            filaFormulario.appendChild(formulario);
            columna2.append(filaFormulario);

            // 🔥 Detectar el parámetro 'v' en la URL
            const urlParams = new URLSearchParams(window.location.search);
            const vParametro = urlParams.get("v");

            if (vParametro && vParametro !== "0") {

// 🔥 Verificar que se han recibido los parámetros necesarios
if (!idClinica || !idVet) {
    console.error("❌ Faltan parámetros en la URL.");
    document.getElementById("horarios_container").innerHTML = "<p>Error: Faltan datos para mostrar la agenda.</p>";
} else {


        // 🔥 Crear columna3 para contener la tabla y el formulario
        const columna3 = document.createElement("div");
        columna3.classList.add("columna-3");
        
        // Crear formulario
        const formulario = document.createElement("form");
        formulario.method = "GET";
        formulario.action = "agendar.html";

        // Fechas (próximos 7 días)
        const hoy = new Date();
        let fechas = [];
        for (let i = 0; i < 7; i++) {
            let fecha = new Date(hoy);
            fecha.setDate(hoy.getDate() + i);
            fechas.push(fecha.toISOString().split("T")[0]); // Formato YYYY-MM-DD
        }

        // Horas disponibles
        const horas = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"];

        // Crear tabla
        const tabla = document.createElement("table");
        tabla.classList.add("horarios-tabla");

        // Crear encabezado de la tabla con los días
        const thead = document.createElement("thead");
        const trHead = document.createElement("tr");
        trHead.innerHTML = "<th>Hora</th>"; // Primera columna vacía
        fechas.forEach(fecha => {
            trHead.innerHTML += `<th>${fecha}</th>`; // Encabezado con fechas
        });
        thead.appendChild(trHead);
        tabla.appendChild(thead);

        // Crear cuerpo de la tabla con horarios
        const tbody = document.createElement("tbody");

        horas.forEach(hora => {
            const fila = document.createElement("tr");

            // Primera columna con la hora
            const tdHora = document.createElement("td");
            tdHora.textContent = hora;
            fila.appendChild(tdHora);

            // Verificar si la hora está ocupada en el DF `data`
            fechas.forEach(fecha => {
                const td = document.createElement("td");
                td.dataset.fecha = fecha;
                td.dataset.hora = hora;

                // 🔍 Buscar si esta fecha y hora están ocupadas
                const ocupado = data.some(registro => 
                    registro.id_clinica == idClinica &&
                    registro.id_vet == idVet &&
                    registro.fecha === fecha &&
                    registro.hora === hora
                );

                if (ocupado) {
                    td.textContent = "X";
                    td.classList.add("ocupado");
                } else {
                    td.textContent = "✔";
                    td.classList.add("disponible");
                    td.addEventListener("click", function () {
                        document.getElementById("input_fecha").value = fecha;
                        document.getElementById("input_hora").value = hora;
                    });
                }
                fila.appendChild(td);
            });

            tbody.appendChild(fila);
        });

        tabla.appendChild(tbody);
        horariosContainer.appendChild(tabla);

        // Agregar campos ocultos para enviar los datos seleccionados
        const inputClinica = document.createElement("input");
        inputClinica.type = "hidden";
        inputClinica.name = "id_clinica";
        inputClinica.value = idClinica;

        const inputVet = document.createElement("input");
        inputVet.type = "hidden";
        inputVet.name = "v";
        inputVet.value = idVet;

        const inputFecha = document.createElement("input");
        inputFecha.type = "hidden";
        inputFecha.name = "dia";
        inputFecha.id = "input_fecha";

        const inputHora = document.createElement("input");
        inputHora.type = "hidden";
        inputHora.name = "hora";
        inputHora.id = "input_hora";

        // Botón de envío
        const botonSubmit = document.createElement("button");
        botonSubmit.type = "submit";
        botonSubmit.textContent = "Agendar";

        formulario.append(inputClinica, inputVet, inputFecha, inputHora, botonSubmit);
        horariosContainer.appendChild(formulario);
        columna3.appendChild(formulario);

        // Agregar columna3 al contenedor principal
        document.getElementById("horarios_container").appendChild(columna3);

    }
                


                contenedor.appendChild(columna3);
                contenedor.append(columna1, columna2, columna3);
            }else{
                contenedor.append(columna1, columna2);
            }   
  


            resultadosContainer.appendChild(contenedor);
        })
        .catch(error => {
            resultadosContainer.innerHTML = `<p>Error al cargar los datos: ${error}</p>`;
        });
});


