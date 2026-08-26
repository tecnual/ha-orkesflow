# Orkesflow - Integración para Home Assistant 🏠📋

Integración oficial de **Orkesflow** para Home Assistant. Permite sincronizar tableros de tareas, tareas del hogar (*chores*) y listas de la compra como entidades nativas `todo` en Home Assistant.

## 🚀 Características

- **Dominio Nativo `todo`:** Gestiona tus tableros y listas desde la tarjeta oficial `todo-list` de Home Assistant, Google Assistant, Alexa o Siri.
- **Selección Dinámica de Tableros:** Selecciona en el flujo de configuración exactamente qué tableros deseas tener en Home Assistant.
- **Sincronización Híbrida:** Polling periódico asíncrono + soporte de Webhooks para actualizaciones al instante.
- **Acciones / Servicios:** Añade ítems o completa tareas desde cualquier automatización de Home Assistant.

## 📦 Instalación mediante HACS

1. Abre **HACS** en tu Home Assistant.
2. Haz clic en los tres puntos de la esquina superior derecha y selecciona **Repositorios personalizados**.
3. Añade la URL de este repositorio, selecciona la categoría **Integración** y pulsa **Añadir**.
4. Busca **Orkesflow** e instálalo.
5. Reinicia Home Assistant.

## ⚙️ Configuración

1. En Home Assistant, ve a **Ajustes > Dispositivos y Servicios > Añadir Integración**.
2. Busca **Orkesflow**.
3. Introduce la **URL del servidor Orkesflow** (ej. `http://192.168.1.100:3000` o `https://app.orkesflow.com`) y tu **Personal Access Token (PAT)**.
4. Selecciona los tableros que deseas importar como entidades `todo`.
