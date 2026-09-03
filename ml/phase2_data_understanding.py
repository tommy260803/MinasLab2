import json

def get_data_understanding_report():
    """Genera el reporte formal de la Fase 2 de CRISP-DM."""
    report = {
        "phase": "2 - Data Understanding",
        "data_sources": [
            "PostgreSQL -> Tabla 'equipments': Metadatos de la flota (Tipos, Fechas de compra, Estado actual).",
            "PostgreSQL -> Tabla 'sensors': Catálogo de sensores físicos (Unidades, Umbrales max/min permitidos).",
            "PostgreSQL -> Tabla 'sensor_readings': Big Data de telemetría IoT. Registro de valores por timestamp.",
            "PostgreSQL -> Tabla 'maintenances': Bitácora de mantenimiento (Tipos, Fechas de intervención)."
        ],
        "variables_description": {
            "TEMPERATURA": "Continua (°C). Típico: 80-90. Crítico > 110. Indica sobrecalentamiento del motor.",
            "PRESION": "Continua (PSI). Típico: 90-110. Baja presión indica fugas hidráulicas.",
            "VIBRACION": "Continua (mm/s). Monitorea ejes y rodamientos. Alza sostenida previene roturas.",
            "RPM": "Continua (Rev/Min). Régimen del motor. Dispersión alta indica anomalía.",
            "NIVEL_ACEITE": "Continua (%). Típico: >60%. Niveles bajos desencadenan fallas catastróficas.",
            "reading_timestamp": "Datetime. Variable temporal clave para series de tiempo y orden crónico.",
            "equipment_type": "Categórica nominal. CAMION_EXTRACCION, PALA_HIDRAULICA, PERFORADORA.",
            "status": "Categórica nominal. OPERATIVO, EN_MANTENIMIENTO, FUERA_DE_SERVICIO.",
            "maintenance_type": "Categórica nominal. PREVENTIVO, CORRECTIVO, PREDICTIVO.",
            "failure_probability": "Continua [0,1]. Resultado histórico de iteraciones previas del modelo."
        },
        "data_quality_anomalies_summary": (
            "1. Ausencia de nulos sistemáticos reportados por los sensores. "
            "2. Duplicados marginales por latencia de red IoT. "
            "3. Anomalías detectadas: Picos aislados de Z-Score > 3 en Temperatura y RPM que podrían "
            "ser ruido del sensor (Outliers) o fallas inminentes reales. "
            "4. Desbalanceo natural: Hay muchos más registros operativos (Normal) que horas de falla (Anomalía)."
        )
    }
    return report

def run_phase2():
    print("="*50)
    print("📊 FASE 2: COMPRENSIÓN DE LOS DATOS (Data Understanding)")
    print("="*50)
    report = get_data_understanding_report()
    
    print("\n🗄️ INVENTARIO DE FUENTES DE DATOS:")
    for source in report["data_sources"]:
        print(f"  - {source}")
        
    print("\n📖 DICCIONARIO DE VARIABLES (Top 10+ operacionales y de negocio):")
    for k, v in report["variables_description"].items():
        print(f"  - [{k}]: {v}")
        
    print("\n⚠️ RESUMEN DE CALIDAD DE DATOS Y ANOMALÍAS:")
    print(report["data_quality_anomalies_summary"])
    
    # Guardar documentación
    with open("ml/phase2_data_understanding.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print("\n[+] Reporte de la Fase 2 guardado en ml/phase2_data_understanding.json")

if __name__ == "__main__":
    run_phase2()
