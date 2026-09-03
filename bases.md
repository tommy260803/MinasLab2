UNIVERSIDAD NACIONAL DE TRUJILLO
VICERRECTORADO ACADÉMICO
ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS
________________________________________

📘 GUÍA DE PRÁCTICA DE LABORATORIO N° 02
DESARROLLO DE UNA APLICACIÓN WEB CON INTELIGENCIA ARTIFICIAL PARA GESTIÓN DE MANTENIMIENTO PREDICTIVO

________________________________________
📋 DATOS GENERALES
Concepto	Detalle
Curso	Ingeniería de Software II
Código	IS-402
Semestre Académico	2026 - II
Docente	Ing. [Nombre del Docente]
Duración	4 sesiones de 2 horas (8 horas cronológicas)
Trabajo	Grupos de 2 alumnos
Semestre	VIII
Prerrequisitos	Programación Orientada a Objetos, Bases de Datos I, Estructuras de Datos
Fecha de entrega	Sesión 2 de la práctica
________________________________________
1. FUNDAMENTACIÓN TEÓRICA
1.1 Ingeniería de Software y Aplicaciones Empresariales
La ingeniería de software es una disciplina que aplica principios de ingeniería para desarrollar software de calidad. En la actualidad, las aplicaciones empresariales integran cada vez más componentes de inteligencia artificial para proporcionar valor agregado a los procesos de negocio.
En el contexto peruano, la industria minera representa uno de los pilares económicos más importantes, y la optimización de los procesos de mantenimiento de equipos de carguío mediante técnicas de IA puede generar ahorros significativos y reducir tiempos de inactividad.
1.2 Metodología CRISP-DM
CRISP-DM (Cross-Industry Standard Process for Data Mining) es la metodología estándar de la industria para proyectos de minería de datos y ciencia de datos. Consta de 6 fases:
1.	Comprensión del Negocio - Definir objetivos y requisitos desde la perspectiva del negocio
2.	Comprensión de los Datos - Recolectar, explorar y familiarizarse con los datos iniciales
3.	Preparación de los Datos - Limpiar, transformar y construir el conjunto de datos final
4.	Modelado - Construir, entrenar y calibrar modelos de IA
5.	Evaluación - Medir el rendimiento y seleccionar el mejor modelo
6.	Despliegue - Integrar el modelo en la aplicación y ponerlo en producción
1.3 Algoritmos de Inteligencia Artificial
Algoritmos Tradicionales (Machine Learning Clásico):
•	Random Forest: Ensemble de múltiples árboles de decisión. Alta interpretabilidad, robusto al sobreajuste, maneja bien relaciones no lineales.
•	XGBoost: Implementación optimizada de Gradient Boosting. Alto rendimiento predictivo, maneja regularización integrada.
•	SVM (Support Vector Machines): Máquinas de Vectores de Soporte. Efectivo en espacios de alta dimensionalidad, sólido fundamentación matemática.
Algoritmos Híbridos (Deep Learning + ML):
•	CNN-LSTM: Combina Redes Neuronales Convolucionales (CNN) para extracción automática de características locales + Redes LSTM para capturar dependencias temporales en series de datos.
•	LSTM-Autoencoder + RF: Autoencoder LSTM para reducción no lineal de dimensionalidad + Random Forest para la clasificación final. Combina lo mejor de ambos mundos.
1.4 Tecnologías Web Modernas
•	Streamlit: Framework Python de código abierto para crear aplicaciones web interactivas de manera rápida y sencilla, sin necesidad de conocimientos de frontend.
•	PostgreSQL: Sistema de gestión de bases de datos relacional objeto-relacional, robusto, escalable y con características avanzadas.
•	JWT (JSON Web Tokens): Estándar abierto para la transmisión segura de información entre partes como un objeto JSON.
•	bcrypt: Biblioteca de hashing de contraseñas diseñada para ser segura y resistente a ataques de fuerza bruta.
________________________________________
2. OBJETIVOS
2.1 Objetivo General
Desarrollar una aplicación web completa usando Python + Streamlit + PostgreSQL que implemente un motor de inteligencia artificial para mantenimiento predictivo de equipos industriales, aplicando la metodología CRISP-DM y principios de ingeniería de software.
2.2 Objetivos Específicos
1.	✅ Diseñar e implementar una base de datos relacional en PostgreSQL con al menos 8 tablas
2.	✅ Desarrollar un sistema de autenticación con 4 roles y matriz de permisos de usuario
3.	✅ Implementar un dashboard interactivo con KPIs y visualizaciones interactivas
4.	✅ Aplicar análisis exploratorio de datos (EDA) sobre datos de sensores industriales
5.	✅ Entrenar y evaluar comparativamente 3 algoritmos de IA tradicionales y 2 híbridos
6.	✅ Implementar validación cruzada, optimización de hiperparámetros y pruebas estadísticas robustas
7.	✅ Desarrollar módulo de generación de reportes en PDF, Word y Excel
8.	✅ Aplicar principios de modularidad, reutilización y documentación de código
________________________________________
3. COMPETENCIAS A DESARROLLAR
Competencia	Descriptor del Nivel de Logro
Resuelve problemas	Aplica conocimientos de ingeniería de software para resolver problemas complejos de la industria minera local
Diseña arquitecturas	Diseña arquitecturas de software multicapa integrando componentes de inteligencia artificial
Implementa soluciones	Desarrolla aplicaciones web modernas con persistencia en bases de datos relacionales
Evalúa modelos	Aplica métodos estadísticos robustos para validar y comparar modelos de IA
Trabaja en equipo	Colabora efectivamente en equipos de 3 personas, usando control de versiones
Documenta	Elabora documentación técnica y reportes profesionales en múltiples formatos
________________________________________
4. EQUIPOS Y MATERIALES
4.1 Software Requerido
Software	Versión Mínima	Enlace de Descarga
Python	3.10	https://www.python.org/downloads/
PostgreSQL	14	https://www.postgresql.org/download/
pgAdmin	4	https://www.pgadmin.org/download/
Git	2.3	https://git-scm.com/downloads
Visual Studio Code	1.80	https://code.visualstudio.com/
4.2 Librerías Python Principales
# Instalación básica
pip install streamlit pandas numpy plotly

# Machine Learning
pip install scikit-learn xgboost imbalanced-learn

# Deep Learning (opcional pero recomendado)
pip install tensorflow

# Base de datos
pip install psycopg2-binary

# Reportes
pip install reportlab python-docx openpyxl

# Seguridad
pip install PyJWT bcrypt

# Estadística y visualización
pip install scipy seaborn
________________________________________
5. METODOLOGÍA CRISP-DM APLICADA
El proyecto seguirá estrictamente las 6 fases de CRISP-DM adaptadas al contexto de mantenimiento predictivo en minería:
🔹 FASE 1: Comprensión del Negocio
•	Problema: Alta frecuencia de fallas no detectadas en equipos de carguío minero
•	Objetivos de negocio: Reducir MTTR ≥20%, aumentar disponibilidad ≥5%, reducir costos ≥15%
•	Criterios de éxito del modelo: Precisión ≥85%, Sensibilidad ≥90%, F1 ≥0.85
•	Requisito de velocidad: Inferencia < 1 segundo por predicción
🔹 FASE 2: Comprensión de los Datos
•	Fuentes de datos: Sensores de temperatura, presión de aceite, RPM, vibraciones, horas de operación
•	Variables a monitorizar: 10+ parámetros de operación de equipos
•	Análisis exploratorio: Estadísticas descriptivas, distribuciones, correlaciones, detección de outliers
🔹 FASE 3: Preparación de los Datos
•	Limpieza: Tratamiento de nulos, eliminación de duplicados, corrección de outliers
•	Transformación: Normalización/estandarización, codificación de variables categóricas
•	Ingeniería de características: Ventanas deslizantes, estadísticas móviles, indicadores de degradación
•	División: 70% entrenamiento, 15% validación, 15% prueba (preservando orden temporal)
🔹 FASE 4: Modelado
Entrenamiento de los 5 algoritmos: 1. Random Forest (tradicional) 2. XGBoost (tradicional) 3. SVM (tradicional) 4. CNN-LSTM (híbrido) 5. LSTM-Autoencoder + RF (híbrido)
🔹 FASE 5: Evaluación
•	Métricas: Accuracy, Precision, Recall, F1-Score, AUC-ROC, AUC-PR
•	Validación cruzada: K-Fold, Stratified K-Fold, Time Series Split
•	Optimización de hiperparámetros: Grid Search, Random Search
•	Pruebas estadísticas: Prueba t pareada, McNemar, sensibilidad al ruido, estabilidad bootstrap
🔹 FASE 6: Despliegue
•	Integración del mejor modelo en la aplicación Streamlit
•	Persistencia de modelos entrenados en disco
•	Interfaz web para predicción bajo demanda
•	Generación de reportes automáticos
