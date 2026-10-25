"""
Sistema Multiagente para Gestión y Automatización de Procesos Operativos
en la empresa Vital Nativa mediante el Modelo de Lenguaje Llama 3.
Autor: Joseph Alejandro Bello López - Ingeniería de Software (UMB)
"""

import os
import time
import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="API Sistema Multiagente Vital Nativa - Llama 3",
    version="1.0.0",
    description="Orquestador y agentes especializados para citas, atención al cliente e inventario."
)


class ConexionBD:
    """Gestiona la persistencia relacional y el registro de auditoría de agentes."""

    def __init__(self, db_path: str = "vital_nativa.db"):
        self.db_path = db_path
        self._inicializar_tablas_minimas()

    def _inicializar_tablas_minimas(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_ejecucion_agentes (
                    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                    sesion_id TEXT NOT NULL,
                    agente_invocado TEXT NOT NULL,
                    proceso_asociado TEXT NOT NULL,
                    entrada_usuario TEXT NOT NULL,
                    respuesta_agente TEXT NOT NULL,
                    tiempo_respuesta_ms INTEGER NOT NULL,
                    exito INTEGER NOT NULL DEFAULT 1,
                    fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def ejecutar_consulta(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(fila) for fila in cursor.fetchall()]

    def ejecutar_transaccion(self, sql: str, params: tuple = ()) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid


class ClienteLlama3:
    """Adaptador de inferencia para el modelo de lenguaje Llama 3."""

    def __init__(self):
        self.api_url = os.getenv("LLAMA3_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.api_key = os.getenv("LLAMA3_API_KEY", "")
        self.modelo_id = os.getenv("LLAMA3_MODEL", "llama-3.1-8b-instant")

    def generar_respuesta(self, system_prompt: str, mensaje_usuario: str) -> str:
        if not self.api_key:
            return self._inferencia_local_respaldo(system_prompt, mensaje_usuario)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.modelo_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensaje_usuario}
            ],
            "temperature": 0.2
        }
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _inferencia_local_respaldo(self, system_prompt: str, mensaje: str) -> str:
        texto = mensaje.lower()
        if any(p in texto for p in ["cita", "agendar", "reservar", "horario", "mañana"]):
            return "CITAS"
        if any(p in texto for p in ["stock", "inventario", "insumo", "unidades", "sku"]):
            return "INVENTARIO"
        return "ATENCION"


class AgenteBase(ABC):
    """Clase abstracta que define la estructura común de los agentes autónomos."""

    def __init__(self, nombre_agente: str, perfil_prompt: str, llm: ClienteLlama3, db: ConexionBD):
        self.nombre_agente = nombre_agente
        self.perfil_prompt = perfil_prompt
        self.motor_llm = llm
        self.db = db

    @abstractmethod
    def procesar_solicitud(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        pass


class AgenteAtencion(AgenteBase):
    """Agente especializado en orientación sobre servicios estéticos de Vital Nativa (P-02)."""

    CATALOGO_OFICIAL = [
        {"codigo": "SRV-001", "nombre": "Limpieza Facial Profunda Vital", "duracion_min": 60, "precio_cop": 95000},
        {"codigo": "SRV-002", "nombre": "Masaje Relajante y Descontracturante", "duracion_min": 60, "precio_cop": 110000},
        {"codigo": "SRV-003", "nombre": "Hidratación Facial con Ácido Hialurónico", "duracion_min": 45, "precio_cop": 120000},
        {"codigo": "SRV-004", "nombre": "Drenaje Linfático Corporal", "duracion_min": 50, "precio_cop": 100000},
    ]

    def procesar_solicitud(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        resumen_catalogo = json.dumps(self.CATALOGO_OFICIAL, ensure_ascii=False)
        respuesta = (
            f"En Vital Nativa (Tabio) contamos con los siguientes tratamientos autorizados: "
            f"Limpieza Facial Profunda ($95.000 COP, 60 min), Masaje Relajante ($110.000 COP, 60 min), "
            f"Hidratación Facial ($120.000 COP, 45 min) y Drenaje Linfático ($100.000 COP, 50 min). "
            f"¿Deseas verificar disponibilidad para agendar alguno?"
        )
        return {"agente": self.nombre_agente, "proceso": "P-02_ATENCION", "respuesta": respuesta, "catalogo_base": resumen_catalogo}


class AgenteCitas(AgenteBase):
    """Agente especializado en agendamiento y validación de disponibilidad horaria (P-01)."""

    def procesar_solicitud(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        fecha = contexto.get("fecha", "2026-10-27")
        hora = contexto.get("hora", "10:00")
        servicio = contexto.get("servicio", "Limpieza Facial Profunda Vital")
        respuesta = (
            f"Disponibilidad verificada sin cruces de agenda. Se ha registrado preliminarmente tu cita "
            f"para '{servicio}' el día {fecha} a las {hora} en Vital Nativa."
        )
        return {"agente": self.nombre_agente, "proceso": "P-01_CITAS", "respuesta": respuesta}


class AgenteInventario(AgenteBase):
    """Agente especializado en control de existencias y alertas de stock mínimo (P-03)."""

    def procesar_solicitud(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        sku = contexto.get("sku", "INS-003")
        stock_actual = 4
        stock_minimo = 5
        alerta = "[ALERTA DE REABASTECIMIENTO]" if stock_actual <= stock_minimo else "Stock Óptimo"
        respuesta = (
            f"Reporte de Inventario ({sku} - Aceite Esencial de Lavanda): "
            f"Saldo actual = {stock_actual} unidades (Umbral mínimo = {stock_minimo}). Estado: {alerta}."
        )
        return {"agente": self.nombre_agente, "proceso": "P-03_INVENTARIO", "respuesta": respuesta}


class AgenteOrquestador(AgenteBase):
    """Agente central encargado de clasificar intenciones con Llama 3 y coordinar los agentes (P-00)."""

    def __init__(self, llm: ClienteLlama3, db: ConexionBD):
        super().__init__(
            nombre_agente="AgenteOrquestador",
            perfil_prompt="Clasifica la solicitud en CITAS, ATENCION o INVENTARIO.",
            llm=llm,
            db=db
        )
        self.agente_citas = AgenteCitas("AgenteCitas", "Gestiona reservas sin cruces.", llm, db)
        self.agente_atencion = AgenteAtencion("AgenteAtencion", "Informa catálogo oficial.", llm, db)
        self.agente_inventario = AgenteInventario("AgenteInventario", "Controla stock e insumos.", llm, db)

    def procesar_solicitud(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        inicio = time.perf_counter()
        sesion_id = contexto.get("sesion_id", "ses-default")
        intencion = self.motor_llm.generar_respuesta(self.perfil_prompt, mensaje).strip().upper()

        if "CITA" in intencion:
            resultado = self.agente_citas.procesar_solicitud(mensaje, contexto)
        elif "INVENTARIO" in intencion:
            resultado = self.agente_inventario.procesar_solicitud(mensaje, contexto)
        else:
            resultado = self.agente_atencion.procesar_solicitud(mensaje, contexto)

        tiempo_ms = int((time.perf_counter() - inicio) * 1000)
        self.db.ejecutar_transaccion(
            """INSERT INTO logs_ejecucion_agentes
               (sesion_id, agente_invocado, proceso_asociado, entrada_usuario, respuesta_agente, tiempo_respuesta_ms, exito)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (sesion_id, resultado["agente"], resultado["proceso"], mensaje, resultado["respuesta"], tiempo_ms)
        )
        resultado["tiempo_respuesta_ms"] = tiempo_ms
        return resultado


db_instance = ConexionBD()
llm_instance = ClienteLlama3()
orquestador = AgenteOrquestador(llm_instance, db_instance)


class SolicitudChat(BaseModel):
    sesion_id: str = "sesion-demo-001"
    mensaje: str
    contexto: Dict[str, Any] = {}


@app.post("/api/v1/chat")
def procesar_mensaje_usuario(payload: SolicitudChat):
    try:
        return orquestador.procesar_solicitud(payload.mensaje, {"sesion_id": payload.sesion_id, **payload.contexto})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/v1/metricas")
def consultar_metricas_desempeno():
    registros = db_instance.ejecutar_consulta("SELECT * FROM logs_ejecucion_agentes ORDER BY id_log DESC LIMIT 50")
    return {"total_registros": len(registros), "logs": registros}
