import json

def get_business_understanding_report():
    """Genera el reporte formal de la Fase 1 de CRISP-DM."""
    report = {
        "phase": "1 - Business Understanding",
        "problem_statement": (
            "El sistema actual experimenta fallas imprevistas en los equipos de carguío minero "
            "(camiones autónomos, palas hidráulicas, perforadoras). Estas fallas resultan en "
            "tiempos de inactividad prolongados, cuellos de botella en la extracción y altos costos "
            "operativos por reparaciones correctivas de emergencia."
        ),
        "business_objectives": {
            "O1_reduce_mttr": "Reducir el Tiempo Medio de Reparación (MTTR) en ≥20% anticipando fallas.",
            "O2_increase_availability": "Aumentar la disponibilidad de la flota en ≥5%.",
            "O3_reduce_costs": "Reducir los costos de mantenimiento no planificado en ≥15% migrando al mantenimiento predictivo."
        },
        "model_success_criteria": {
            "Precision": "≥ 85% (Minimizar falsos positivos para no sacar equipos de operación innecesariamente).",
            "Sensibilidad (Recall)": "≥ 90% (Detectar la gran mayoría de fallas reales, prioridad de negocio).",
            "F1-Score": "≥ 0.85 (Balance adecuado entre Precision y Recall).",
            "AUC-ROC": "≥ 0.90 (Excelente capacidad de discriminación entre estado normal y falla).",
            "AUC-PR": "≥ 0.85 (Manejo robusto de datos desbalanceados, típico en fallas).",
            "Inference Time": "< 1 segundo (Permitir scoring casi en tiempo real desde los sensores IoT)."
        },
        "project_plan": (
            "1. Consolidar telemetría de sensores y órdenes de trabajo (Semanas 1-2). "
            "2. Desarrollo y validación del modelo predictivo (Semanas 3-5). "
            "3. Despliegue e integración en dashboard de operaciones (Semana 6)."
        )
    }
    return report

def run_phase1():
    print("="*50)
    print("🚀 FASE 1: COMPRENSIÓN DEL NEGOCIO (Business Understanding)")
    print("="*50)
    report = get_business_understanding_report()
    
    print("\n🚨 DEFINICIÓN DEL PROBLEMA:")
    print(report["problem_statement"])
    
    print("\n🎯 OBJETIVOS DE NEGOCIO CUANTIFICABLES:")
    for k, v in report["business_objectives"].items():
        print(f"  - {v}")
        
    print("\n✅ CRITERIOS DE ÉXITO DEL MODELO:")
    for k, v in report["model_success_criteria"].items():
        print(f"  - {k}: {v}")
        
    print("\n📝 PLAN DE PROYECTO:")
    print(report["project_plan"])
    
    # Guardar documentación
    with open("ml/phase1_business_understanding.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print("\n[+] Reporte de la Fase 1 guardado en ml/phase1_business_understanding.json")

if __name__ == "__main__":
    run_phase1()
