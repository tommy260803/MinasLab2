# Sistema de Mantenimiento Predictivo de Equipos de Carguío Minero

Proyecto académico para el curso IS-402 (Ingeniería de Software II) de la UNT. Este proyecto implementa una aplicación web basada en Python y Streamlit, apoyada por una base de datos PostgreSQL, para realizar mantenimiento predictivo aplicando la metodología CRISP-DM.

## Arquitectura del Proyecto

- **Presentación:** Streamlit (Python)
- **Lógica de Negocio:** Python modular
- **Persistencia:** PostgreSQL 14+
- **Motor IA:** Algoritmos tradicionales e híbridos (CRISP-DM)

## Requisitos Previos

- Python 3.9 o superior.
- PostgreSQL 14 o superior.
- Git.

## Instrucciones de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd LABORATORIO2_SOFTWARE
   ```

2. **Crear y activar el entorno virtual**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno**
   - Copiar el archivo `.env.example` y renombrarlo a `.env`.
   - Modificar las variables de base de datos (`DB_USER`, `DB_PASSWORD`, etc.) según su configuración local.

5. **Configurar la base de datos**
   - Ejecutar los scripts ubicados en `database/schema.sql` y `database/seed_data.sql` en su servidor PostgreSQL para crear la estructura e insertar datos de prueba.

6. **Ejecutar la aplicación**
   ```bash
   streamlit run app/main.py
   ```

## Estructura de Directorios

- `app/`: Capa de presentación (Streamlit).
- `core/`: Lógica de negocio, autenticación, base de datos.
- `ml/`: Motor de Inteligencia Artificial (CRISP-DM).
- `data/`: Almacenamiento de datasets y modelos entrenados.
- `reports/`: Generación de reportes automáticos.
- `database/`: Scripts SQL.
- `tests/`: Pruebas unitarias.
