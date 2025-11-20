# 🎓 API de Becas CGSU - Backend

API intermediaria desarrollada con FastAPI para manejar la autenticación y lógica de negocio del sistema de becas del Consejo General Sindical Universitario (CGSU).

> ⚠️ **Estado del Proyecto**: Este proyecto se encuentra actualmente en **desarrollo activo**. Los endpoints actuales son funcionales, pero se están agregando nuevas características constantemente.

## 🚀 Características

- ✅ Autenticación de usuarios con Supabase
- ✅ Registro de nuevos usuarios
- ✅ Inicio de sesión seguro
- ✅ CORS configurado para desarrollo
- ✅ Documentación automática con Swagger
- ✅ Desplegado en Vercel

## 🛠️ Tecnologías Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno y rápido para Python
- **[Supabase](https://supabase.com/)** - Base de datos PostgreSQL con autenticación
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI de alto rendimiento
- **[Pydantic](https://pydantic.dev/)** - Validación de datos
- **[Python-dotenv](https://pypi.org/project/python-dotenv/)** - Manejo de variables de entorno

## 🚧 Estado de Desarrollo

Este proyecto está en **desarrollo activo**. Actualmente cuenta con funcionalidades básicas de autenticación y se están desarrollando las siguientes características:

### ✅ Completado:
- Sistema de autenticación completo (registro/login)
- Conexión con base de datos Supabase
- Documentación automática con Swagger
- Despliegue automático en Vercel
- Configuración CORS para frontend

### 🔄 En Desarrollo:
- **API Privada**: Implementación de autenticación JWT y endpoints protegidos
- **Gestión de Becas**: Endpoints para crear, leer, actualizar y eliminar becas
- **Sistema de Filtros**: Búsqueda de becas por categoría, monto, nivel académico
- **Aplicaciones**: Sistema para que usuarios puedan aplicar a becas
- **Historial**: Tracking de aplicaciones por usuario

### 📅 Próximamente:
- Panel de administración
- Sistema de notificaciones
- Reportes y estadísticas
- API para gestión de documentos

## 📋 Prerrequisitos

- Python 3.8+
- pip
- Git

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/EduardoGMora/BecasCGSU-Back.git
cd BecasCGSU-Back
```

### 2. Crear entorno virtual

```bash
python -m venv .venv

# En Windows
.venv\Scripts\activate

# En macOS/Linux
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
cd FastApi
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

1. Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Edita el archivo `.env` con tus credenciales de Supabase:
```env
SUPABASE_URL="tu_supabase_url"
SUPABASE_ANON_KEY="tu_supabase_anon_key"
```

### 5. Ejecutar la aplicación

```bash
cd FastApi
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

La API estará disponible en: `http://localhost:3000`

## 📚 Documentación de la API

### Endpoints Disponibles (v1.0.0)

| Método | Endpoint | Descripción | Estado |
|--------|----------|-------------|---------|
| GET | `/` | Mensaje de bienvenida | ✅ Funcionando |
| POST | `/register` | Registro de nuevos usuarios | ✅ Funcionando |
| POST | `/login` | Inicio de sesión | ✅ Funcionando |

### 🚧 Endpoints en Desarrollo (Próximamente)

Los siguientes endpoints están siendo desarrollados y estarán disponibles en futuras versiones:

| Método | Endpoint | Descripción | Estado |
|--------|----------|-------------|---------|
| GET | `/becas` | Obtener todas las becas disponibles | 🔄 En desarrollo |
| GET | `/becas?categoria={categoria}` | Filtrar becas por categoría | 🔄 En desarrollo |
| GET | `/becas?nivel={nivel}` | Filtrar becas por nivel académico | 🔄 En desarrollo |
| GET | `/becas?monto_min={monto}&monto_max={monto}` | Filtrar becas por rango de monto | 🔄 En desarrollo |
| GET | `/becas/{id}` | Obtener detalles de una beca específica | 🔄 En desarrollo |
| GET | `/usuarios/{user_id}/becas` | Obtener becas aplicadas por un usuario | 🔄 En desarrollo |
| POST | `/becas/{id}/aplicar` | Aplicar a una beca específica | 🔄 En desarrollo |
| GET | `/usuarios/{user_id}/aplicaciones` | Ver historial de aplicaciones del usuario | 🔄 En desarrollo |

### 📋 Roadmap de Funcionalidades

#### Fase 1 - Gestión de Becas (En desarrollo)
- [ ] **Middleware de autenticación JWT** para proteger endpoints
- [ ] CRUD completo para becas
- [ ] Sistema de filtros y búsqueda
- [ ] Categorización de becas
- [ ] Gestión de montos y requisitos
- [ ] **Endpoints privados** protegidos por autenticación

#### Fase 2 - Aplicaciones (Planificado)
- [ ] Sistema de aplicación a becas
- [ ] Tracking de estado de aplicaciones
- [ ] Notificaciones automáticas
- [ ] Historial de aplicaciones

#### Fase 3 - Administración (Planificado)
- [ ] Panel de administración
- [ ] Gestión de usuarios
- [ ] Reportes y estadísticas
- [ ] Sistema de aprobación de becas

### Documentación Interactiva

Una vez que la API esté ejecutándose, puedes acceder a:

- **Swagger UI**: [http://localhost:3000/docs](http://localhost:3000/docs)
- **ReDoc**: [http://localhost:3000/redoc](http://localhost:3000/redoc)

## 🔗 Uso de la API

### 🧪 Pruebas con Postman

#### Configuración para Login/Register:

1. **Método**: POST
2. **URL**: `http://localhost:3000/login` o `http://localhost:3000/register`
3. **Headers**:
   ```
   Content-Type: application/json
   ```
4. **Body** (raw - JSON):
   ```json
   {
     "email": "tu_email@ejemplo.com",
     "password": "tu_contraseña"
   }
   ```

#### Ejemplo de colección Postman:

```json
{
  "info": {
    "name": "API Becas CGSU"
  },
  "item": [
    {
      "name": "Registro",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@ejemplo.com\",\n  \"password\": \"123456\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/register",
          "host": ["{{base_url}}"],
          "path": ["register"]
        }
      }
    }
  ]
}
```

## 🚀 Despliegue

### Vercel

La aplicación está configurada para desplegarse automáticamente en Vercel:

1. Conecta tu repositorio con Vercel
2. Las variables de entorno se configuran en el dashboard de Vercel
3. El archivo `vercel.json` ya está configurado

**URL de producción**: [https://becascgsuback.vercel.app](https://becascgsuback.vercel.app)

### Variables de Entorno para Producción

Asegúrate de configurar en Vercel:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## 🗄️ Base de Datos

El proyecto utiliza Supabase como backend de base de datos con las siguientes características:

- **Autenticación**: Manejo automático de usuarios
- **Base de datos**: PostgreSQL
- **Tiempo real**: Funcionalidades en tiempo real disponibles

## 📁 Estructura del Proyecto

```
BecasCGSU-Back/
├── FastApi/
│   ├── main.py              # Aplicación principal
│   ├── requirements.txt     # Dependencias Python
│   ├── vercel.json         # Configuración de Vercel
│   ├── .env                # Variables de entorno (no versionado)
│   └── .env.example        # Ejemplo de variables de entorno
├── Supabase/
│   └── supabase/
│       ├── config.toml     # Configuración de Supabase
│       └── migrations/     # Migraciones de base de datos
└── README.md               # Documentación
```

### 🎯 Áreas donde puedes contribuir:

- **Endpoints de Becas**: Implementación de CRUD para gestión de becas
- **Sistema de Filtros**: Desarrollo de filtros avanzados por categoría, monto, nivel académico
- **Sistema de Aplicaciones**: Funcionalidad para que usuarios apliquen a becas
- **Documentación**: Mejoras en la documentación de endpoints
- **Testing**: Implementación de pruebas unitarias y de integración
- **Performance**: Optimizaciones en consultas y respuestas de la API

## 📝 Notas de Desarrollo

### CORS
La API está configurada para permitir requests desde:
- `http://localhost`
- `http://localhost:3000`
- `http://localhost:5173`

### Seguridad
- Las contraseñas son manejadas por Supabase
- Los tokens JWT son generados automáticamente
- Variables de entorno para datos sensibles
- ⚠️ **Pendiente**: Implementar middleware de autenticación para endpoints privados
- ⚠️ **Pendiente**: Proteger endpoints de gestión de becas con JWT

### Modo Desarrollo
- Auto-reload activado con `--reload`
- Logs detallados en consola
- Documentación automática habilitada

## 🐛 Resolución de Problemas

### Error: "Could not import module 'main'"
- Asegúrate de estar en la carpeta `FastApi/`
- Verifica que `main.py` exista

### Error: "Supabase connection failed"
- Verifica las variables de entorno
- Confirma que las credenciales de Supabase sean correctas

### Error 422: "Unprocessable Entity"
- Verifica que estés enviando JSON en el body
- Asegúrate de incluir `Content-Type: application/json`

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Equipo

- **Desarrollador**: [Aldo105](https://github.com/Aldo105)
- **Desarrollador**: [EduardoGMora](https://github.com/EduardoGMora)
- **Desarrollador**: [Jangel21](https://github.com/Jangel21)
- **Desarrollador**: [AlexUr27](https://github.com/AlexUr27)

## 🔄 Changelog

### v1.0.0 (Actual)
- ✅ Implementación inicial
- ✅ Autenticación con Supabase
- ✅ Endpoints de registro y login
- ✅ Configuración CORS
- ✅ Despliegue en Vercel

### v1.1.0 (En desarrollo)
- 🔄 **Middleware de autenticación JWT** para API privada
- 🔄 **Endpoints protegidos** para gestión de becas
- 🔄 Endpoint para obtener todas las becas
- 🔄 Sistema de filtros para becas
- 🔄 Endpoint para becas por usuario
- 🔄 Gestión de aplicaciones a becas

### v1.2.0 (Planificado)
- 📋 Panel de administración
- 📋 Sistema de notificaciones
- 📋 Reportes y estadísticas

---

Para más información o soporte, abre un issue en el repositorio.
