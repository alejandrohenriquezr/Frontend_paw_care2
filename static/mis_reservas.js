document.addEventListener("DOMContentLoaded", function() {
    const user = getUserInfo(); // Implementa esta función para obtener la información del usuario autenticado
    const nombreUsuario = user.name;
    const correoUsuario = user.email;

    const mensajeBienvenida = document.getElementById("mensaje_bienvenida");
    mensajeBienvenida.innerHTML = `Bienvenido ${nombreUsuario} a tu página de citas agendadas.`;

    cargarReservas(correoUsuario);

    document.getElementById("cerrar_sesion").addEventListener("click", function() {
        cerrarSesion();
    });

    function cargarReservas(correo) {
        // Implementa la lógica para cargar las reservas desde reservas.csv
        // Filtra por correo y muestra las reservas en una tabla con paginación
    }

    function cerrarSesion() {
        // Implementa la lógica para cerrar la sesión de Google y redirigir a index.html
        alert("Sesión cerrada. Redirigiendo a la página principal.");
        window.location.href = "index.html";
    }

    function getUserInfo() {
        // Implementa la lógica para obtener la información del usuario autenticado
        return { name: "Nombre de Usuario", email: "usuario@correo.com" }; // Ejemplo
    }
});