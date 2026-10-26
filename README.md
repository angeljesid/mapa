# 🗺️ Visor Geográfico - Bloque Garcero C (Auditoría ANLA)

![Render](https://img.shields.io/badge/Render-Deployed-success?style=for-the-badge&logo=render)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker)

Plataforma web interactiva desarrollada para la presentación, análisis espacial y consulta de datos del proyecto Bloque Garcero C. Esta herramienta está diseñada específicamente para facilitar la visualización de evidencias y la consulta de información técnica durante los procesos de auditoría y licenciamiento ambiental ante la ANLA.

## ✨ Características Principales

*   **Cartografía Digital Interactiva:** Visor geográfico que permite la exploración de capas espaciales relacionadas con el área de influencia del proyecto.
*   **Asistente Virtual IA:** Chat interactivo procesado mediante Python para consultar rápidamente detalles técnicos, normativas y datos del entorno geográfico.
*   **Exploración Multimedia:** Galería integrada para la visualización fluida de imágenes estáticas y recorridos en video directamente en la interfaz.
*   **Arquitectura Portable:** Entorno completamente contenerizado que garantiza su ejecución estable sin depender de configuraciones locales específicas.

## 🛠️ Stack Tecnológico

*   **Frontend:** HTML5, CSS3, JavaScript (Leaflet.js)
*   **Backend & IA:** Python
*   **Infraestructura:** Docker, Docker Compose
*   **Despliegue Cloud:** Render

## 🚀 Acceso al Proyecto (Web)

El visor se encuentra desplegado y accesible en la nube para evaluación directa.

🔗 **URL Pública:** [https://mapa-fc0m.onrender.com/](https://mapa-fc0m.onrender.com/)

*(Nota: Al estar alojado en una instancia sin servidor dedicado continuo, la plataforma puede tomar ~50 segundos en mostrar la pantalla inicial si ha estado inactiva. Las consultas y la navegación posteriores se ejecutarán a velocidad normal).*

## 💻 Despliegue Local (Desarrolladores)

Para ejecutar el proyecto en un entorno local aislado, se requiere [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. Clona este repositorio:
   ```bash
   git clone [https://github.com/angeljesid/mapa.git](https://github.com/angeljesid/mapa.git)
