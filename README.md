# Job Finder CV 🔍

Aplicación web que analiza tu CV con IA y encuentra ofertas de trabajo acordes a tu perfil.

## Características

- **Subir CV en PDF** → Claude extrae automáticamente tus habilidades, experiencia y perfil profesional
- **Múltiples perfiles** → guarda y gestiona varios CVs, cambia entre ellos desde el panel lateral
- **Perfil protegido** → la información se muestra en modo lectura; hay que pulsar "Editar" para modificar cada bloque
- **Buscar ofertas** por puesto, ubicación y rango de experiencia
- **APIs reales** → conecta con Adzuna e InfoJobs; si no hay claves configuradas usa datos de demo
- **Resiliencia de APIs** → funciona aunque solo tengas una API disponible, sin errores bloqueantes
- **Match IA** → cada oferta recibe una puntuación de compatibilidad con tu perfil (0–100 %)
- **Desglose del match** → habilidades que coinciden y las que te faltan por adquirir
- **Trazas en LangSmith** → visualiza cada llamada al LLM (opcional)

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| UI | Streamlit |
| LLM | Claude Haiku 4.5 (Anthropic) |
| Orquestación | LangChain 0.3 (LCEL) |
| Observabilidad | LangSmith (opcional) |
| Parsing PDF | PyPDF2 |
| APIs de empleo | Adzuna · InfoJobs |
| Almacenamiento | JSON local |

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/envio_cvs.git
cd envio_cvs
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus claves:

**Anthropic API Key** *(obligatoria)*
1. Ve a [console.anthropic.com](https://console.anthropic.com) → API Keys
2. Crea una clave y pégala en `ANTHROPIC_API_KEY`

**Adzuna** *(opcional — ofertas reales)*
1. Ve a [developer.adzuna.com](https://developer.adzuna.com) y regístrate
2. En el Dashboard copia el `App ID` y el `App Key`
3. Pégalos en `ADZUNA_APP_ID` y `ADZUNA_APP_KEY`

**InfoJobs** *(opcional — ofertas reales)*
1. Ve a [developer.infojobs.net](https://developer.infojobs.net) y registra tu app
2. Pega las credenciales en `INFOJOBS_CLIENT_ID` e `INFOJOBS_CLIENT_SECRET`

**LangSmith** *(opcional — trazabilidad)*
1. Crea cuenta en [smith.langchain.com](https://smith.langchain.com)
2. Ve a *Settings → API Keys* y pega la clave en `LANGSMITH_API_KEY`
3. Cambia `LANGSMITH_TRACING=false` a `true` para activar las trazas

> Si no configuras ninguna API de empleo la app funciona igualmente con datos de demo.

### 4. Ejecutar la aplicación

**Windows** — doble clic en `iniciar_app.bat`

**Cualquier sistema**:
```bash
streamlit run app/main.py
```

La app se abre en `http://localhost:8501`.

## Uso

1. **Sube tu CV** (PDF) en el panel lateral → pulsa **"Analizar CV"**
2. Claude extrae tu perfil: nombre, puesto, habilidades, experiencia y educación
3. Revisa los datos en la pestaña **Mi Perfil** — cada bloque se puede editar por separado
4. Ve a **Buscar empleos**, introduce el puesto y la ubicación que quieres
5. Ajusta el filtro de años de experiencia e incluye o excluye el trabajo en remoto
6. Pulsa **"Buscar empleos"** — la IA puntúa cada oferta y explica el resultado
7. Las ofertas aparecen ordenadas de mayor a menor compatibilidad (🟢 ≥ 70 % · 🟡 ≥ 40 % · 🔴 < 40 %)

## Estructura del proyecto

```
envio_cvs/
├── app/
│   ├── main.py                    # Entrada Streamlit (UI completa)
│   ├── config.py                  # Variables de entorno y setup LangSmith
│   ├── cv_parser.py               # Extracción de texto de PDF (PyPDF2)
│   ├── job_search.py              # Búsqueda, filtrado y agregación de ofertas
│   ├── profile_manager.py         # Gestión de múltiples perfiles en JSON
│   ├── apis/
│   │   ├── adzuna.py              # Integración API Adzuna
│   │   └── infojobs.py            # Integración API InfoJobs
│   └── chains/
│       ├── cv_extraction_chain.py # Chain: PDF → CVProfile estructurado
│       └── job_matching_chain.py  # Chain: perfil + oferta → JobMatch (0–100)
├── data/
│   ├── mock_jobs.json             # Ofertas de demo (usadas sin claves API)
│   └── profiles/                  # Perfiles guardados localmente (ignorado en git)
├── iniciar_app.bat                # Lanzador rápido para Windows
├── .env.example                   # Plantilla de configuración
├── .gitignore
├── requirements.txt
└── README.md
```

## Gestión de perfiles

La app soporta múltiples perfiles simultáneos. Cada perfil se guarda como un archivo JSON en `data/profiles/` con el nombre derivado del campo "Nombre del perfil". Desde el panel lateral puedes:

- Cambiar entre perfiles con el selector desplegable
- Eliminar un perfil con el botón 🗑️
- Añadir un nuevo perfil subiendo otro PDF

## Observabilidad con LangSmith

Con LangSmith activado, cada búsqueda genera trazas visibles en [smith.langchain.com](https://smith.langchain.com) bajo el proyecto `envio-cvs`:

- El PDF completo que recibió Claude para analizar el CV
- El perfil estructurado que extrajo
- Cómo puntuó cada oferta y el razonamiento
- Latencia y consumo de tokens de cada llamada

El plan gratuito incluye 5.000 trazas/mes, más que suficiente para uso personal.
