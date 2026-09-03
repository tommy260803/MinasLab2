# Pendientes del Sistema de Mantenimiento Predictivo

## Resumen Ejecutivo

| # | Pendiente | Gravedad | Estado |
|---|---|---|---|
| 1 | Pruebas unitarias vacías | **Crítica** | 🔴 |
| 2 | Carpeta `reports/` vacía e inconsistente | Alta | 🟠 |
| 3 | Dependencias faltantes en `requirements.txt` | Media | 🟡 |
| 4 | `ml/phase6_deployment.py` vacío | Media | 🟡 |
| 5 | Columna `details` ausente en `schema.sql` | Baja | 🟢 |

---

## 1. Pruebas Unitarias Vacías (CRÍTICA)

**Ubicación:** `tests/`

| Archivo | Líneas | Estado |
|---|---|---|
| `tests/test_auth.py` | 0 | Vacío |
| `tests/test_db.py` | 0 | Vacío |
| `tests/test_ml.py` | 0 | Vacío |

**Impacto:**
- Incumplimiento del objetivo del proyecto: "Aplicar principios de modularidad, reutilización y documentación de código".
- Sin validación de que la lógica de autenticación, base de datos y ML funciona correctamente.
- `pytest` está en `requirements.txt` pero no se usa.

**Qué debe implementarse:**
- `test_auth.py`: pruebas de hash bcrypt, generación/verificación JWT, flujo de login exitoso/fallido.
- `test_db.py`: pruebas de conexión a BD, ejecución de queries, migraciones.
- `test_ml.py`: pruebas de funciones de `phase3_data_preparation.py` (clean_data, feature_engineering, split_and_scale) y validación de modelos entrenados.

---

## 2. Carpeta `reports/` Vacía e Inconsistente (ALTA)

**Ubicación:** `reports/`

| Archivo | Estado |
|---|---|
| `reports/__init__.py` | Vacío |
| `reports/pdf_generator.py` | Vacío (0 líneas) |
| `reports/word_generator.py` | Vacío (0 líneas) |
| `reports/excel_generator.py` | Vacío (0 líneas) |

**Problema:**
- La funcionalidad de generación de reportes está en `core/report_generator.py` (160 líneas, completamente funcional).
- Los archivos vacíos en `reports/` crean confusión sobre dónde está la lógica real.
- El `reports_view.py` importa desde `core.report_generator`, no desde `reports/`.

**Solución:**
- **Opción A:** Mover la lógica de `core/report_generator.py` a `reports/` y actualizar los imports en `app/components/reports_view.py`.
- **Opción B:** Eliminar los archivos vacíos de `reports/` y documentar que la funcionalidad está en `core/`.

---

## 3. Dependencias Faltantes en `requirements.txt` (MEDIA)

**Ubicación:** `requirements.txt`

**Dependencias ausentes detectadas:**

| Paquete | Uso en el código | Archivo que lo importa |
|---|---|---|
| `scipy` | `stats.ttest_rel` para pruebas estadísticas | `ml/phase5_evaluation.py:8` |
| `imbalanced-learn` | Mencionado en especificaciones para manejo de desbalanceo | `bases.md:83` |
| `seaborn` | Mencionado en especificaciones para visualización | `bases.md:98` |

**Impacto:**
- Ejecutar `pip install -r requirements.txt` no instala todas las dependencias necesarias.
- `phase5_evaluation.py` fallará si `scipy` no está instalado.

---

## 4. `ml/phase6_deployment.py` Vacío (MEDIA)

**Ubicación:** `ml/phase6_deployment.py` — 0 líneas.

**Problema:**
- La Fase 6 de CRISP-DM (Deployment) no tiene implementación como script independiente.
- La lógica de despliegue está integrada en `app/components/deployment_view.py` (287 líneas).
- No hay forma de ejecutar la Fase 6 desde línea de comandos como las demás fases.

**Impacto:**
- Inconsistencia con las demás fases (1-5) que sí tienen scripts ejecutables.
- Dificulta la automatización del pipeline CRISP-DM.

**Solución:**
- Crear `ml/phase6_deployment.py` con una función `run_phase6()` que sirva como wrapper o punto de entrada, documentando que la lógica principal está en la vista Streamlit.

---

## 5. Columna `details` Ausente en `schema.sql` (BAJA)

**Ubicación:** `database/schema.sql`

**Problema:**
- La tabla `audit_logs` definida en `schema.sql` no tiene la columna `details`.
- `core/db_manager.py` la agrega dinámicamente en runtime via:
  ```sql
  ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS details TEXT
  ```
- Esto funciona pero es frágil: depende de que la migración se ejecute antes de cualquier inserción.

**Solución:**
- Agregar la columna `details TEXT` directamente en `schema.sql` dentro de la definición de `audit_logs`.
- Mantener el ALTER TABLE como fallback seguro.

---

## Archivos Completos (No requieren acción)

| Componente | Estado |
|---|---|
| `core/` (5 módulos) | ✅ Completo |
| `database/schema.sql` + `seed_data.sql` | ✅ Completo |
| `data/` (modelos + datos procesados) | ✅ Completo |
| `.env.example` | ✅ Completo |
| `config.yaml` | ✅ Completo |
| `ml/` (fases 1-5 + algoritmos) | ✅ Completo |
| `app/components/` (6 vistas) | ✅ Completo |
| `app/main.py` | ✅ Completo |
