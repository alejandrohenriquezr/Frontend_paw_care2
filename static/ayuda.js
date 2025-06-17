let modoPasadas = false;
document.addEventListener("DOMContentLoaded", function () {
    const btnayuda = document.querySelector("#btn-ayuda");
    const btnfaq = document.querySelector("#btn-faq");
    const btncontacto = document.querySelector("#btn-contacto");
    const btnprivacidad = document.querySelector("#btn-privacidad");

    const divAyuda = document.querySelector("#div-ayuda");
    const divFaq = document.querySelector("#div-faq");
    const divContacto = document.querySelector("#div-contacto");
    const divPrivacidad = document.querySelector("#div-privacidad");

    
    btnayuda.addEventListener("click", () => {
        modoPasadas = false;
        btnayuda.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        divAyuda.classList.remove("hidden");
        divFaq.classList.add("hidden");
        divContacto.classList.add("hidden");
        divPrivacidad.classList.add("hidden");
        divAyuda.scrollIntoView({ behavior: "smooth" });

        
        btnfaq.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnfaq.classList.add("text-neutral-500");
        btncontacto.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btncontacto.classList.add("text-neutral-500");
        btnprivacidad.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnprivacidad.classList.add("text-neutral-500");             

      });
  
      btnfaq.addEventListener("click", () => {
        modoPasadas = false;
        btnfaq.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        
        divAyuda.classList.add("hidden");
        divFaq.classList.remove("hidden");
        divContacto.classList.add("hidden");
        divPrivacidad.classList.add("hidden");
        divFaq.scrollIntoView({ behavior: "smooth" });

        btnayuda.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnayuda.classList.add("text-neutral-500");
        btncontacto.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btncontacto.classList.add("text-neutral-500");
        btnprivacidad.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnprivacidad.classList.add("text-neutral-500");             

      });
  
  
      btncontacto.addEventListener("click", () => {
        modoPasadas = false;
        btncontacto.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        divAyuda.classList.add("hidden");
        divFaq.classList.add("hidden");
        divContacto.classList.remove("hidden");
        divPrivacidad.classList.add("hidden");
        divContacto.scrollIntoView({ behavior: "smooth" });
        
        btnayuda.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnayuda.classList.add("text-neutral-500");
        btnfaq.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnfaq.classList.add("text-neutral-500");
        btnprivacidad.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnprivacidad.classList.add("text-neutral-500");             

      });

  
      btnprivacidad.addEventListener("click", () => {
        modoPasadas = false;
        btnprivacidad.classList.add("border-b-2", "border-neutral-700", "text-neutral-700");
        divAyuda.classList.add("hidden");
        divFaq.classList.add("hidden");
        divContacto.classList.add("hidden");
        divPrivacidad.classList.remove("hidden");
        divPrivacidad.scrollIntoView({ behavior: "smooth" });
        
        btnayuda.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnayuda.classList.add("text-neutral-500");
        btnfaq.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btnfaq.classList.add("text-neutral-500");
        btncontacto.classList.remove("border-b-2", "border-neutral-700", "text-neutral-700");
        btncontacto.classList.add("text-neutral-500");             

      });

    // Por omisión: mostrar próximas citas
    btnayuda.click();
  });
  

  
