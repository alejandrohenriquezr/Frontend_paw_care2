let modoPasadas = false;
document.addEventListener("DOMContentLoaded", function () {
    const btnProximas = document.querySelector("#btn-proximas");
    const btnPasadas = document.querySelector("#btn-pasadas");
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    console.log("hoy en mis citas es=", hoy);  
    

    
    btnProximas.addEventListener("click", () => {
        modoPasadas = false;
        aplicarTodosLosFiltros();
        btnProximas.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        btnPasadas.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnPasadas.classList.add("text-neutral-500");
        //ocultamos el botón evaluar_cita y mostramos el boton cancelar_cita
        document.querySelectorAll(".evaluar_cita").forEach(btn => {
          btn.style.display = "none";
        });
        document.querySelectorAll(".cancelar_cita").forEach(btn => {
          btn.style.display = "block";
        });      

      });
  
    btnPasadas.addEventListener("click", () => {
      modoPasadas = true;
      aplicarTodosLosFiltros();
      btnPasadas.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
      btnProximas.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
      btnProximas.classList.add("text-neutral-500");

      //ocultamos el botón cancelar_cita y mostramos el boton evaluar_cita
      document.querySelectorAll(".cancelar_cita").forEach(btn => {
        btn.style.display = "none";
      });
      document.querySelectorAll(".evaluar_cita").forEach(btn => {
        btn.style.display = "block";
      });      

    });
  
    // Por omisión: mostrar próximas citas
    btnProximas.click();
  });
  

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".cancelar_cita").forEach(btn => {
      btn.addEventListener("click", async function () {
        const confirmado = confirm("¿Estás seguro de que deseas cancelar esta cita?");
        if (!confirmado) return;
  
        const id_clinica = this.dataset.id_clinica;
        const correo = this.dataset.correo;
        const fecha = this.dataset.fecha;
        console.log("id_clinica=", id_clinica, " correo=", correo, "fecha= ", fecha);
        const res = await fetch('/cancelar_cita', {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ id_clinica, correo, fecha })
        });
  
        const data = await res.json();
        if (data.success) {
          this.textContent = "Eliminada";
          this.classList.remove("bg-red-500", "hover:bg-red-600");
          this.classList.add("bg-red-200", "text-red-800");
          this.disabled = true;
  
          const statusSpan = this.closest(".datos_reserva").querySelector(".estado_cita");
          if (statusSpan) {
            statusSpan.textContent = "Eliminada";
            statusSpan.classList.remove("bg-green-200", "text-green-800");
            statusSpan.classList.add("bg-red-200", "text-red-800");
          }
        } else {
          alert("Error al cancelar la cita.");
        }
      });
    });
  });

  
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".confirmar_cita").forEach(btn => {
      btn.addEventListener("click", async function () {
        const confirmado = confirm("¿Estás seguro de que deseas confirmar esta cita?");
        if (!confirmado) return;
  
        const id_reserva = this.dataset.id_reserva;
        console.log("id_reserva=", id_reserva);
        const res = await fetch('/confirmar_cita', {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ id_reserva })
        });
  
        const data = await res.json();
        if (data.success) {
          this.textContent = "Pagada";
          this.classList.remove("bg-red-500", "hover:bg-red-600");
          this.classList.add("bg-green-200", "text-red-800");
          this.disabled = true;
          /*  
          const statusSpan = this.closest(".datos_reserva").querySelector(".estado_cita");
          if (statusSpan) {
            statusSpan.textContent = "Eliminada";
            statusSpan.classList.remove("bg-green-200", "text-green-800");
            statusSpan.classList.add("bg-red-200", "text-red-800");
          }
            */
        } else {
          alert("Error al cancelar la cita.");
        }
      });
    });
  });


  document.addEventListener("DOMContentLoaded", function () {
    // Render estrellas por cada fila
    function renderStars(container) {
      container.innerHTML = '';
      for (let i = 1; i <= 5; i++) {
        const star = document.createElement("span");
        star.innerHTML = "&#9733;";
        star.className = "cursor-pointer text-white border border-blue-500 px-2 py-1";
        star.dataset.valor = i;
        container.appendChild(star);
      }
    }
  
    // Manejo de click en botón evaluar
    document.querySelectorAll(".evaluar_cita").forEach(btn => {
      btn.addEventListener("click", () => {
        const reserva = btn.dataset.reserva;
        const nombre = btn.closest(".datos_reserva").querySelector(".nombre_clinica").textContent;
        document.getElementById("titulo_modal").innerText = `Evalúa a la clínica ${nombre}`;
        document.getElementById("modal_evaluacion").classList.remove("hidden");
        document.getElementById("form_evaluacion").dataset.reserva = reserva;
  
        document.querySelectorAll(".estrellas").forEach(div => renderStars(div));
        document.getElementById("enviar_evaluacion").disabled = true;
      });
    });
  
    // Interacción de estrellas
    document.addEventListener("click", e => {
      if (e.target.closest(".estrellas span")) {
        const span = e.target;
        const container = span.parentElement;
        const valor = parseInt(span.dataset.valor);
        container.dataset.valor = valor;
  
        container.querySelectorAll("span").forEach((s, i) => {
          s.classList.remove("bg-blue-500");
          s.classList.add("text-white");
          if (i < valor) {
            s.classList.add("bg-blue-500");
          }
        });
  
        if (container.dataset.tipo === "general") {
          document.getElementById("enviar_evaluacion").disabled = false;
        }
      }
    });
  
    // Cancelar modal
    document.getElementById("cancelar_modal").addEventListener("click", () => {
      document.getElementById("modal_evaluacion").classList.add("hidden");
    });
  
    // Enviar formulario
    document.getElementById("form_evaluacion").addEventListener("submit", async (e) => {
      e.preventDefault();
      const reserva = e.target.dataset.reserva;
  
      const data = {
        reserva,
        general: parseInt(document.querySelector('[data-tipo="general"]').dataset.valor || 0),
        puntualidad: parseInt(document.querySelector('[data-tipo="puntualidad"]').dataset.valor || 0),
        precio_calidad: parseInt(document.querySelector('[data-tipo="precio-calidad"]').dataset.valor || 0)
      };
  
      const res = await fetch("/evaluar_cita", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
  
      if (res.ok) {
        //alert("¡Evaluación registrada correctamente!");
        document.getElementById("modal_evaluacion").classList.add("hidden");
        // Cambiar el botón "Evalúa Cita" a "Evaluada"
        const btnEvaluar = document.querySelector(`.evaluar_cita[data-reserva="${reserva}"]`);
        if (btnEvaluar) {
          btnEvaluar.textContent = "Evaluada";
          btnEvaluar.disabled = true;
          btnEvaluar.classList.remove("bg-blue-500", "hover:bg-red-600");
          btnEvaluar.classList.add("bg-green-300", "text-green-900");
        }
        alert("Gracias por evaluar nuestros servicios. Te hemos enviado un correo con la información de la evaluación.");

      } else {
        alert("Error al guardar la evaluación.");
      }
    });
  });

  //Para llenar los botones select de clínicas, veterinarios y mascotas
  document.addEventListener("DOMContentLoaded", function () {
    const selectClinicas = document.getElementById("clinicas");
    const selectVeterinarios = document.getElementById("veterinarios");
    const selectMascotas = document.getElementById("mascotas");
    const selectEstados = document.getElementById("estados");
  
    const citas = document.querySelectorAll(".cita-item");
  
    const nombresClinicas = new Set();
    const nombresVeterinarios = new Set();
    const nombresMascotas = new Set();
    const estadosDisponibles  = new Set();
  
    citas.forEach(cita => {
      const nombreClinica = cita.querySelector(".nombre_clinica")?.textContent.trim();
      const nombreMascota = cita.querySelector(".nombre_mascota")?.textContent.trim();
      const nombreVeterinario = cita.querySelector(".nombre_veterinario")?.textContent.trim();
      const estado = cita.querySelector(".estado_cita")?.textContent.trim();

      if (nombreClinica) nombresClinicas.add(nombreClinica);
      if (nombreMascota) nombresMascotas.add(nombreMascota);
      if (nombreVeterinario) nombresVeterinarios.add(nombreVeterinario);
      if (estado) estadosDisponibles.add(estado);
    });
  
    // Función para llenar un select
    function llenarSelect(select, opciones, textoBase) {
      select.innerHTML = "";
      const optionTodos = document.createElement("option");
      optionTodos.textContent = textoBase;
      optionTodos.value = "";
      select.appendChild(optionTodos);
  
      opciones.forEach(valor => {
        const option = document.createElement("option");
        option.textContent = valor;
        option.value = valor;
        select.appendChild(option);
      });
    }
  
    llenarSelect(selectClinicas, Array.from(nombresClinicas).sort(), "Todas las clínicas");
    llenarSelect(selectMascotas, Array.from(nombresMascotas).sort(), "Todas las mascotas");
    llenarSelect(selectVeterinarios, Array.from(nombresVeterinarios).sort(), "Todos los veterinarios");
    llenarSelect(document.getElementById("estados"), Array.from(estadosDisponibles).sort(), "Todos los estados");

  });
  
  document.addEventListener("DOMContentLoaded", function () {
    const selectClinicas = document.getElementById("clinicas");
    const selectVeterinarios = document.getElementById("veterinarios");
    const selectMascotas = document.getElementById("mascotas");
    const selectEstados = document.getElementById("estados");
  
      
    // Escuchar cambios en los selects
    selectClinicas.addEventListener("change", aplicarTodosLosFiltros);
    selectVeterinarios.addEventListener("change", aplicarTodosLosFiltros);
    selectMascotas.addEventListener("change", aplicarTodosLosFiltros);
    selectEstados.addEventListener("change", aplicarTodosLosFiltros);
    document.getElementById("buscador").addEventListener("input", aplicarTodosLosFiltros);

    aplicarTodosLosFiltros();
  });
  

  function aplicarTodosLosFiltros() {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
  
    const valorClinica = document.getElementById("clinicas").value;
    const valorVeterinario = document.getElementById("veterinarios").value;
    const valorMascota = document.getElementById("mascotas").value;
    const valorEstado = document.getElementById("estados").value;
    const textoLibre = document.getElementById("buscador").value.trim().toLowerCase();

    document.querySelectorAll(".cita-item").forEach(cita => {
      const nombreClinica = cita.querySelector(".nombre_clinica")?.textContent.trim();
      const nombreVeterinario = cita.querySelector(".nombre_veterinario")?.textContent.trim();
      const nombreMascota = cita.querySelector(".nombre_mascota")?.textContent.trim();
      const estadoCita = cita.querySelector(".estado_cita")?.textContent.trim();
      const textoTotal = `
        ${nombreClinica || ""}
        ${nombreVeterinario || ""}
        ${nombreMascota || ""}
        ${estadoCita || ""}
      `.toLowerCase();

      const coincideTextoLibre = !textoLibre || textoTotal.includes(textoLibre);


      const partes = cita.dataset.fecha.split("-");
      const fecha = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
      fecha.setHours(0, 0, 0, 0);
      const esPasada = (fecha < hoy);
  
      const coincideClinica = !valorClinica || nombreClinica === valorClinica;
      const coincideVeterinario = !valorVeterinario || nombreVeterinario === valorVeterinario;
      const coincideMascota = !valorMascota || nombreMascota === valorMascota;
      const coincideEstado = !valorEstado || estadoCita === valorEstado;
      const coincideFecha = (modoPasadas && esPasada) || (!modoPasadas && !esPasada);
  
      if (coincideClinica && 
        coincideVeterinario && 
        coincideMascota && 
        coincideEstado && 
        coincideFecha &&
        coincideTextoLibre) {
        cita.style.display = "block";
      } else {
        cita.style.display = "none";
      }
    });
    // Mostrar u ocultar mensaje si no hay resultados
    const hayResultados = Array.from(document.querySelectorAll(".cita-item")).some(
      cita => cita.style.display !== "none"
    );

    const mensaje = document.getElementById("mensaje-sin-citas");
    if (mensaje) {
      mensaje.classList.toggle("hidden", hayResultados); // ocultar si hay resultados
    }

  }
  