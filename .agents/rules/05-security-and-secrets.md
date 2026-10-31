# Regla 05: Seguridad, Secretos y Límites de Entorno

## 1. Política de Cero Secretos en Repositorio
- Jamás incluir en commits credenciales, tokens API, contraseñas, claves privadas ni cadenas de conexión con credenciales reales.
- Todo secreto debe gestionarse mediante variables de entorno (`.env` incluido en `.gitignore`) o bóvedas seguras.
- Proporcionar siempre un `.env.example` con claves ficticias y explicaciones de configuración.

## 2. Validación Fail-Closed
- Cualquier petición sin autenticar o con permisos insuficientes debe ser rechazada inmediatamente en la capa más externa posible.
- Sanitizar rigurosamente todas las entradas de usuario para prevenir inyecciones (SQL, XSS, Command Injection).
