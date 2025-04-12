document.addEventListener("DOMContentLoaded", function () {
    const btnProximas = document.querySelector("#btn-proximas");
    const btnPasadas = document.querySelector("#btn-pasadas");
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
  
    function filtrarCitas(pasadas = false) {
        document.querySelectorAll(".cita-item").forEach(cita => {
            const fecha = new Date(cita.dataset.fecha);
            fecha.setHours(0, 0, 0, 0);
            const esPasada = fecha < hoy;
            if ((pasadas && esPasada) || (!pasadas && !esPasada)) {
            cita.style.display = "block";
            } else {
            cita.style.display = "none";
            }
        });
    }
  
    btnProximas.addEventListener("click", () => {
        filtrarCitas(false);
        btnProximas.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        btnPasadas.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnPasadas.classList.add("text-neutral-500");
    });
  
    btnPasadas.addEventListener("click", () => {
        filtrarCitas(true);
      btnPasadas.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
      btnProximas.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
      btnProximas.classList.add("text-neutral-500");
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
  