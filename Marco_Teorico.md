# Marco Teórico

El presente capítulo profundiza en los fundamentos teóricos y tecnológicos que sustentan el desarrollo de la plataforma "Bank Cost Benchmark API". Se abordan desde las arquitecturas de software moderno hasta los modelos matemáticos utilizados para la proyección de indicadores financieros.

## 1. Arquitectura de Software y Tecnologías Web

Para el desarrollo de aplicaciones web modernas, escalables y mantenibles, es crucial seleccionar una arquitectura que desacople la lógica de negocio de la interfaz de usuario.

### 1.1. Arquitectura Cliente-Servidor y REST API
El patrón de arquitectura **REST (Representational State Transfer)** define un conjunto de restricciones para crear servicios web. En este modelo, el **Backend** (servidor) expone recursos (datos) a través de endpoints HTTP estandarizados (GET, POST, etc.), y el **Frontend** (cliente) consume estos recursos para renderizar la interfaz. Esto permite que ambos compomentes evolucionen de forma independiente.

### 1.2. Frontend: Single Page Application (SPA) con React
Las **Single Page Applications (SPA)** son aplicaciones web que cargan una sola página HTML y actualizan dinámicamente el contenido a medida que el usuario interactúa con la app, sin recargar la página completa.
*   **React:** Biblioteca de JavaScript desarrollada por Facebook para construir interfaces de usuario. Utiliza un **DOM Virtual** para optimizar el renderizado y una arquitectura basada en **Componentes** reutilizables, lo que facilita el desarrollo modular.
*   **Vite:** Herramienta de construcción (build tool) de próxima generación que ofrece un entorno de desarrollo extremadamente rápido gracias al uso de módulos ES nativos en el navegador.

### 1.3. Backend: Microframeworks con Flask
**Flask** es un microframework para Python. A diferencia de frameworks "full-stack" como Django, Flask es ligero y no impone una estructura rígida ni dependencias innecesarias. Esto lo hace ideal para construir **APIs RESTful** eficientes y servicios de microarquitectura, permitiendo integrar fácilmente bibliotecas de ciencia de datos (como Pandas o Scikit-learn).

### 1.4. Contenerización con Docker
**Docker** es una plataforma que permite empaquetar una aplicación y sus dependencias en una unidad estandarizada llamada **contenedor**. Esto garantiza que la aplicación funcione de la misma manera en cualquier entorno (desarrollo, pruebas, producción), eliminando el problema de "funciona en mi máquina".

## 2. Machine Learning y Predicción Financiera

El núcleo analítico de la plataforma se basa en la capacidad de predecir comportamientos futuros de indicadores económicos clave.

### 2.1. Series de Tiempo (Time Series)
Una serie de tiempo es una secuencia de puntos de datos indexados en orden cronológico. En finanzas, esto es fundamental para analizar la evolución de activos, acciones o indicadores macroeconómicos.
*   **Estacionalidad:** Patrones que se repiten a intervalos regulares (ej. inflación mensual).
*   **Tendencia:** Dirección a largo plazo de la serie (ej. alcista o bajista).

### 2.2. Modelo ARIMA
El modelo **ARIMA (AutoRegressive Integrated Moving Average)** es una de las técnicas más robustas para el pronóstico de series temporales. Se compone de tres partes:
*   **AR (AutoRegressive):** Utiliza la relación dependiente entre una observación actual y observaciones previas.
*   **I (Integrated):** Aplica diferenciación a los datos para hacer la serie estacionaria (eliminar tendencias).
*   **MA (Moving Average):** Utiliza la dependencia entre una observación y el error residual de un modelo de media móvil aplicado a observaciones retrasadas.

En este proyecto, se utiliza la librería `pmdarima` para la selección automática de los hiperparámetros óptimos (p,d,q) del modelo ARIMA (`auto_arima`), maximizando la precisión del pronóstico.

### 2.3. Métricas de Evaluación
Para validar la precisión de los modelos predictivos, se utilizan métricas estandarizadas:
*   **MAPE (Mean Absolute Percentage Error):** Mide el tamaño del error en términos porcentuales. Es fácil de interpretar para stakeholders no técnicos. Un MAPE bajo (ej. < 5%) indica un modelo altamente preciso.

## 3. Contexto Económico y Financiero

La aplicación opera sobre un dominio específico: el mercado financiero chileno y sus indicadores regulatorios.

### 3.1. Indicadores Macroeconómicos
*   **UF (Unidad de Fomento):** Unidad de cuenta reajustable según la inflación, utilizada en Chile para préstamos hipotecarios y otros instrumentos financieros. Su predicción es crítica para la planificación financiera.
*   **IPC (Índice de Precios al Consumidor):** Medida principal de la inflación interna. La variación del IPC determina el valor de la UF.
*   **Bonos del Tesoro (Treasury Yields):** Las tasas de los bonos del tesoro de EE.UU. (ej. 10 años) actúan como tasa libre de riesgo de referencia global, afectando los costos de financiamiento internacional.

### 3.2. Costo Total Anual (CTA)
El **CTA** es un indicador obligatorio en Chile que resume todos los costos asociados a un producto financiero (tasas de interés, comisiones, seguros) en un solo porcentaje anual. Permite comparar productos de diferentes instituciones de manera estandarizada y transparente.

## 4. Inteligencia Artificial Generativa y LLMs

Para mejorar la interacción con el usuario y ofrecer insights cualitativos, se integran tecnologías de Procesamiento de Lenguaje Natural (NLP).

### 4.1. Large Language Models (LLMs)
Modelos de aprendizaje profundo entrenados con inmensas cantidades de texto (ej. Gemini, GPT). Son capaces de entender instrucciones complejas, resumir información y generar texto coherente.

### 4.2. Generación Aumentada por Recuperación (RAG)
Para que un LLM sea útil en un contexto específico (finanzas chilenas), no basta con su conocimiento pre-entrenado. **RAG (Retrieval-Augmented Generation)** es una técnica donde se "inyecta" información relevante (ej. el valor actual de la UF o el ranking de costos calculado por la API) en el prompt del modelo antes de que este genere una respuesta. Esto asegura que las respuestas sean precisas, actualizadas y directamente relevantes para los datos del usuario.
