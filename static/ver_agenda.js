document.addEventListener("DOMContentLoaded", function () {
  const id_veterinario = parseInt(document.getElementById("id_veterinario_agenda").value);
  const agendaContainer = document.getElementById("agenda-container");
  let reservasPorFecha = {};
  let todasHoras = [];
  let fechasOrdenadas = [];
  let pagina = 0; // índice de semana

  async function cargarDatos() {
      //const datosVeterinario = { datos_veterinario };
      console.log("Datos del veterinario en cargarDatos: ", id_veterinario);
      const response = await fetch(`/api/agenda/${id_veterinario}`);
      const data = await response.json();

      // Agrupar por día
      reservasPorFecha = {};
      data.forEach(entry => {
          if (!reservasPorFecha[entry.fecha]) {
              reservasPorFecha[entry.fecha] = [];
          }
          reservasPorFecha[entry.fecha].push(entry.hora);
      });

      fechasOrdenadas = Object.keys(reservasPorFecha).sort((a, b) => {
          const [d1, m1, y1] = a.split("/").map(Number);
          const [d2, m2, y2] = b.split("/").map(Number);
          return new Date(y1, m1 - 1, d1) - new Date(y2, m2 - 1, d2);
      });

      // Todas las horas únicas, ordenadas
      todasHoras = [...new Set(data.map(e => e.hora))].sort();

      renderAgenda();
  }

  function renderAgenda() {
      const inicio = pagina * 7;
      const fin = inicio + 7;
      const diasSemana = fechasOrdenadas.slice(inicio, fin);

      let html = `
      <div class="flex justify-between items-center mb-2">
          <button id="btn-prev" class="text-sm text-[#5A8F99] font-semibold hover:underline" ${pagina === 0 ? "disabled" : ""}>&larr; Semana anterior</button>
          <button id="btn-next" class="text-sm text-[#5A8F99] font-semibold hover:underline" ${(fin >= fechasOrdenadas.length) ? "disabled" : ""}>Semana siguiente &rarr;</button>
      </div>
      <div class="overflow-x-auto rounded-lg border border-gray-300 shadow-sm">
      <table class="min-w-full text-sm text-center text-gray-700">
          <thead class="bg-[#5A8F99] text-white">
              <tr>${diasSemana.map(dia => `<th class="px-4 py-2">${dia}</th>`).join("")}</tr>
          </thead>
          <tbody>`;

      todasHoras.forEach(hora => {
          html += "<tr>";
          diasSemana.forEach(fecha => {
              const horas = reservasPorFecha[fecha] || [];
              html += horas.includes(hora)
                  ? `<td class="px-4 py-2 font-semibold text-[#5A8F99]">${hora}</td>`
                  : `<td class="px-4 py-2 text-neutral-300">-</td>`;
          });
          html += "</tr>";
      });

      html += "</tbody></table></div>";
      agendaContainer.innerHTML = html;

      // Agregar eventos a botones
      document.getElementById("btn-prev")?.addEventListener("click", () => {
          if (pagina > 0) {
              pagina--;
              renderAgenda();
          }
      });

      document.getElementById("btn-next")?.addEventListener("click", () => {
          if (fin < fechasOrdenadas.length) {
              pagina++;
              renderAgenda();
          }
      });
  }

  cargarDatos();
});
