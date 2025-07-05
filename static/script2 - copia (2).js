document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const suggestionsContainer = document.getElementById("suggestions");
    const comuna = sessionStorage.getItem("comuna") || "";

    // Buscar sugerencias desde el backend
    async function fetchSugerencias(query) {
        const res = await fetch(`/api/sugerencias_busqueda?q=${encodeURIComponent(query)}&comuna=${encodeURIComponent(comuna)}`);
        return await res.json();
    }

    // Renderizar sugerencias
    function renderSugerencias(data) {
        suggestionsContainer.innerHTML = "";
        if (!data.length) {
            const noResult = document.createElement("div");
            noResult.textContent = "No se encontraron resultados.";
            noResult.className = "px-4 py-2 text-gray-500";
            suggestionsContainer.appendChild(noResult);
            suggestionsContainer.classList.remove("hidden");
            return;
        }
        console.log("la data en renderSugerencias es:");
        console.log(data);
        data.forEach(item => {
            const div = document.createElement("div");
            div.className = "cursor-pointer px-4 py-2 hover:bg-blue-100 flex items-center gap-2";
            let iconHTML = "";

            if (item.tipo === "especialidad") iconHTML = '<i class="fas fa-dog text-blue-500"></i>';
            else if (item.tipo === "clínica") iconHTML = '<i class="fas fa-hospital text-green-500"></i>';
            else if (item.tipo === "staff") iconHTML = '<i class="fas fa-user-md text-purple-500"></i>';

            div.innerHTML = `${iconHTML} <span>${item.label}</span>`;
            div.addEventListener("click", () => {
                searchInput.value = item.label;
                suggestionsContainer.classList.add("hidden");
                sessionStorage.setItem("busqueda", item.label);
                window.location.href = `/resultados?comuna=${encodeURIComponent(comuna)}&search=${encodeURIComponent(item.label)}`;
            });
            suggestionsContainer.appendChild(div);
        });

        suggestionsContainer.classList.remove("hidden");
    }

    // Al escribir en el input
    searchInput.addEventListener("input", async () => {
        const query = searchInput.value.trim();
        const data = await fetchSugerencias(query);
        console.log("la data es:");
        console.log(data);
        renderSugerencias(data);
    });

    // Al hacer foco (mostrar especialidades por omisión)
    searchInput.addEventListener("focus", async () => {
        console.log("Entrnado al focus");
        const data = await fetchSugerencias("");
        console.log("la data en focus es:");
        console.log(data);
        renderSugerencias(data);
    });

    // Ocultar al hacer click fuera
    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.classList.add("hidden");
        }
    });
});

