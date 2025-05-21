document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".btn-editar-mascota").forEach(boton => {
      boton.addEventListener("click", () => {
        const contenedor = boton.closest(".mascota-container");
        const pesoElemento = contenedor.querySelector(".peso-mascota");
        const idMascota = boton.dataset.id;
        //alert(pesoElemento.textContent);
        //si pesoElemento contiene "kg"
        if (pesoElemento.textContent.includes(" kg")) {
           // alert("Contiene kg");
            pesoActual = pesoElemento.textContent.replace(" kg", "").trim();
        }else{
            //definimos a pesoActual como el valor de pesoElemento
            pesoActual = pesoElemento.textContent;
        }

        const input = document.createElement("input");
        input.type = "number";
        input.value = pesoActual;
        input.className = "border rounded px-2 py-1 w-24";
        pesoElemento.replaceWith(input);
        input.focus();
        //seleccionamos el contenido de imput
        input.select();
        boton.textContent = "Guardar";
        boton.classList.add("btn-guardar");
  
        boton.addEventListener("click", async () => {
          const nuevoPeso = input.value;
  
          const respuesta = await fetch("/actualizar_peso_mascota", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              id_mascota: idMascota,
              nuevo_peso: nuevoPeso
            })
          });
  
          const data = await respuesta.json();
          if (data.success) {
            const nuevoElemento = document.createElement("p");
            nuevoElemento.className = "text-lg text-[#4A4A4A] peso-mascota";
            nuevoElemento.textContent = `${nuevoPeso} kg`;
            input.replaceWith(nuevoElemento);
            boton.textContent = "Editar Información";
            boton.classList.remove("btn-guardar");
          } else {
            alert("Error al guardar el nuevo peso.");
          }
        }, { once: true });
      });
    });
  });
  

  document.querySelectorAll("input[type='file'][id^='file-input-']").forEach(input => {
    input.addEventListener("change", async () => {
      const idMascota = input.dataset.id;
      const archivo = input.files[0];
      if (!archivo) return;
  
      const formData = new FormData();
      formData.append("foto", archivo);
      formData.append("id_mascota", idMascota);
  
      const resp = await fetch("/subir_foto_mascota", {
        method: "POST",
        body: formData
      });
  
      const resultado = await resp.json();
      if (resultado.success) {
        const img = document.getElementById(`foto-mascota-${idMascota}`);
        img.src = `${img.src.split("?")[0]}?t=${new Date().getTime()}`; // cache busting
      } else {
        alert("Error al subir la imagen.");
      }
    });
  });
  