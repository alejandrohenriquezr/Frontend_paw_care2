document.addEventListener("DOMContentLoaded", function () {
    const idClinica = new URLSearchParams(window.location.search).get("id_clinica");
    const calendarioContainer = document.getElementById("form-container");
    const resultados = document.getElementById("resultados_disponibilidad");
    const modalConfirmar = document.getElementById("modal_confirmar");
    const btnConfirmar = document.getElementById("confirmar_reserva_btn");
    let datosReserva = {};
  
    // Cargar feriados desde API pública
    let feriadosChile = [];
  
    fetch("https://apis.digital.gob.cl/fl/feriados")
      .then(res => res.json())
      .then(data => {
        feriadosChile = data.map(d => d.fecha);
        renderizarCalendario();
      })
      .catch(() => {
        feriadosChile = [];
        renderizarCalendario();
      });
  
    function renderizarCalendario() {
      const hoy = new Date();
      const año = hoy.getFullYear();
      const mes = hoy.getMonth();
      const diasMes = new Date(año, mes + 1, 0).getDate();
  
      let tabla = `<input type="hidden" id="id_clinica" value="${idClinica}">
      <h3 class="text-xl font-bold mb-4 text-center">Selecciona una fecha</h3>
      <table class="w-full border text-center">
        <thead class="bg-blue-500 text-white">
          <tr>${["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"].map(d => `<th>${d}</th>`).join("")}</tr>
        </thead>
        <tbody><tr>
      `;
  
      let primerDia = new Date(año, mes, 1).getDay(); // 0=domingo
      primerDia = (primerDia + 6) % 7;
  
      for (let i = 0; i < primerDia; i++) {
        tabla += "<td></td>";
      }
  
      for (let dia = 1; dia <= diasMes; dia++) {
        const fecha = new Date(año, mes, dia);
        const fechaISO = fecha.toISOString().split("T")[0];
  
        const esDomingo = fecha.getDay() === 0;
        const esFeriado = feriadosChile.includes(fechaISO);
        const esPasado = fecha < new Date().setHours(0, 0, 0, 0);
  
        let clase = "cursor-pointer p-2 hover:bg-blue-200";
        if (esPasado) {
          clase = "text-gray-400";
        } else if (esDomingo || esFeriado) {
          clase += " bg-red-200";
        }
  
        tabla += `<td class="${clase}" data-fecha="${fechaISO}">${dia}</td>`;
  
        if ((dia + primerDia) % 7 === 0) tabla += "</tr><tr>";
      }
  
      tabla += "</tr></tbody></table>";
      calendarioContainer.innerHTML = tabla;
  
      document.querySelectorAll("[data-fecha]").forEach(btn => {
        btn.addEventListener("click", () => {
          const fecha = btn.dataset.fecha;
          fetch(`/agendar?id_clinica=${idClinica}&fecha=${fecha}`)
            .then(res => res.json())
            .then(disponibilidad => mostrarDisponibilidad(disponibilidad, fecha));
        });
      });
    }
  
    function mostrarDisponibilidad(disponibilidad, fecha) {
      resultados.innerHTML = "";
      if (disponibilidad.length === 0) {
        resultados.innerHTML = `<p class="text-center text-gray-500">No hay disponibilidad para esta fecha.</p>`;
        return;
      }
  
      disponibilidad.forEach(vet => {
        const div = document.createElement("div");
        div.className = "bg-white p-4 rounded-lg shadow flex items-center justify-between";
  
        div.innerHTML = `
          <div>
            <div class="text-sm text-blue-700 font-bold">${vet.hora}</div>
            <div class="text-gray-700">${vet.nombres} ${vet.apellidos}</div>
            <div class="text-xs text-gray-500">Especialidades: ${vet.especialidades.join(", ")}</div>
          </div>
          <div class="flex items-center space-x-4">
            <img src="/static/images/veterinario${vet.id_veterinario}.jpg" alt="vet" class="w-16 h-16 rounded-full bg-gray-200 object-cover">
            <button
              class="agendar-btn bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
              data-fecha="${fecha}"
              data-hora="${vet.hora}"
              data-correo="${vet.correo}"
            >Agendar</button>
          </div>
        `;
  
        resultados.appendChild(div);
      });
  
      document.querySelectorAll(".agendar-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          datosReserva = {
            id_clinica: parseInt(document.getElementById("id_clinica").value),
            fecha: btn.dataset.fecha,
            hora: btn.dataset.hora,
            correo_veterinario: btn.dataset.correo,
            id_mascota: sessionStorage.getItem("mascotaSeleccionada")
          };
          modalConfirmar.classList.remove("hidden");
        });
      });
    }
  
    btnConfirmar.addEventListener("click", async () => {
      const res = await fetch("/insertar_reserva", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datosReserva)
      });
  
      const json = await res.json();
      if (json.success) {
        alert("Reserva confirmada. Revisa tu correo.");
        window.location.href = "mis_citas";
      } else {
        alert("Ocurrió un error al agendar.");
      }
    });
  });
  