# Sistema Multiagente Vital Nativa (Llama 3)

Repositorio oficial del proyecto de investigación: **"Sistema Multiagente para Gestión y Automatización de Procesos Operativos en empresa de servicios de estética y bienestar 'Vital Nativa' mediante Modelo de lenguaje Llama 3"**.

* **Autor:** Joseph Alejandro Bello López
* **Programa:** Ingeniería de Software - Universidad Manuela Beltrán (UMB)
* **Procesos Automatizados:**
  1. Orquestación y Enrutamiento Conversacional (`AgenteOrquestador`)
  2. Gestión y Agendamiento de Citas (`AgenteCitas`)
  3. Atención y Orientación al Cliente (`AgenteAtencion`)
  4. Control y Gestión de Inventario (`AgenteInventario`)

## Estructura del Proyecto
* `database/schema.sql`: Script DDL y DML del modelo relacional de base de datos (7 tablas e índices).
* `src/main.py`: Implementación del núcleo multiagente, conexión con API de inferencia Llama 3, gestión de base de datos y endpoints REST con FastAPI.
* `requirements.txt`: Dependencias del entorno de ejecución en Python.
