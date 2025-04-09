document.addEventListener("DOMContentLoaded", function() {
    const resultadosContainer = document.getElementById("agendar_resultados");
    const daysContainer = document.getElementById("days");
    const hoursContainer = document.getElementById("hours");

    const urlParams = new URLSearchParams(window.location.search);
    const id_clinica = urlParams.get("id_clinica");
    console.log("ID de la clínicaxxxx:", id_clinica);
    console.log("autenticación es:", isUserAuthenticated());
    const today = new Date();
    const dates = Array.from({ length: 7 }, (_, i) => {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        return date;
    });

    dates.forEach(date => {
        const button = document.createElement("button");
        button.className = "flex-shrink-0 px-6 py-3 rounded-full bg-[#5A8F99] text-white";
        button.textContent = date.toLocaleDateString('es-ES', { weekday: 'long', day: '2-digit', month: '2-digit' });
        button.addEventListener("click", () => showHours(date));
        daysContainer.appendChild(button);
    });

    function showHours(date) {
        hoursContainer.innerHTML = "";
        for (let hour = 10; hour <= 19; hour++) {
            const time = `${hour}:00`;
            const button = document.createElement("button");
            button.className = `flex-shrink-0 px-6 py-3 rounded-full ${hour === 13 || hour === 14 ? 'bg-gray-400' : 'bg-[#5A8F99]'} text-white`;
            button.textContent = time;
            button.disabled = hour === 13 || hour === 14;
            button.addEventListener("click", () => handleTimeClick(date, time));
            hoursContainer.appendChild(button);
        }
    }

    function handleTimeClick(date, time) {
        if (isUserAuthenticated()) {
            const formattedDate = date.toLocaleDateString('es-ES', { weekday: 'long', day: '2-digit', month: '2-digit' });
            window.location.href = `agendar_p2.html?fecha=${formattedDate}&hora=${time}&id_clinica=${id_clinica}`;
        } else {
            alert("Por favor, inicie sesión con su cuenta de Google.");
        }
    }

    function isUserAuthenticated() {
        const auth2 = gapi.auth2.getAuthInstance();
        return auth2.isSignedIn.get();
    }
});