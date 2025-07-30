# Sistema BMS Demo - Módulo 1 🏗️

Sistema de Gestión de Edificios (Building Management System) de demostración para laboratorio con integración Genetec.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-Módulo%201%20Completo-success.svg)

## 📋 Descripción

Este proyecto implementa un sistema BMS de demostración que se integra con un servidor Genetec Security Center para recibir datos de dispositivos físicos (cámaras, controladores de acceso, sensores) y proporcionar una interfaz unificada de monitoreo y control.

### 🎯 Objetivos del Proyecto

- **Laboratorio de Pruebas**: Crear un entorno de desarrollo para probar protocolos BMS
- **Integración Genetec**: Recibir datos del sistema Genetec existente
- **Protocolo Modbus**: Implementar cliente y servidor Modbus TCP/RTU
- **Escalabilidad**: Base sólida para agregar más protocolos (MQTT, BACnet, SNMP, HTTP)
- **Sin Licencias**: Alternativa open-source a sistemas BMS comerciales

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  LABORATORIO PROPUESTO                      │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │   CÁMARAS   │    │CONTROLADORES│    │   GABINETES     │ │
│  │ LABORATORIO │    │LABORATORIO  │    │  LABORATORIO    │ │
│  │             │    │             │    │                 │ │
│  │ • 2-3 Cams  │    │ • 1-2 Doors │    │ • UPS Mini      │ │
│  │ • IP Básicas│    │ • Readers   │    │ • Sensores      │ │
│  └─────────────┘    └─────────────┘    └─────────────────┘ │
│         │                   │                   │          │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         GENETEC SECURITY CENTER                      │  │
│  │         (Misma configuración de producción)          │  │
│  │  • Gestiona cámaras laboratorio                     │  │
│  │  • Controla accesos laboratorio                     │  │
│  │  • Eventos de gabinetes laboratorio                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                             │
│                              │ Modbus TCP/MQTT/HTTP        │
│                              ▼                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            NUESTRO BMS DEMO (SIN LICENCIAS)          │  │
│  │                                                      │  │
│  │  🎯 PROYECTO ACTUAL 🎯                              │  │
│  │  • Recibe datos de Genetec                          │  │
│  │  • Modbus TCP Server/Client                         │  │
│  │  • MQTT Client/Broker                               │  │
│  │  • HTTP/REST API                                    │  │
│  │  • Base de datos propia                             │  │
│  │  • Dashboards web                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Módulo 1 - Características Implementadas

### ✅ Configuración Base
- **Configuración centralizada** con variables de entorno
- **Validación de configuraciones** automática
- **Logging avanzado** con rotación de archivos y colores
- **Base de datos SQLAlchemy** (SQLite por defecto, PostgreSQL/MySQL soportados)

### ✅ Protocolo Modbus (Completo)
- **Cliente Modbus TCP/RTU** para conectar con Genetec
- **Servidor Modbus TCP** para exponer datos del BMS
- **Manejador unificado** que coordina cliente y servidor
- **Cache inteligente** para optimizar lecturas
- **Reconexión automática** en caso de pérdida de conexión
- **Estadísticas detalladas** de operaciones

### ✅ Modelos de Datos
- **Dispositivos**: Cámaras, controladores, sensores, UPS, etc.
- **Sensores**: Temperatura, humedad, presión, etc. con alertas
- **Eventos**: Sistema completo de eventos y alertas
- **Validación robusta** de todos los datos

### ✅ Utilidades
- **Validador**: Validación de IPs, puertos, rangos de sensores
- **Convertidor**: Conversión entre unidades, formatos de datos
- **Constantes**: Configuración centralizada de límites y rangos
- **Logger**: Sistema de logging personalizable y eficiente

## 📁 Estructura del Proyecto

```
sistema_bms_demo/
├── configuracion/
│   ├── configuracion_general.py      # Configuración general del sistema
│   ├── configuracion_protocolos.py   # Configuración de protocolos
│   └── configuracion_base_datos.py   # Configuración de BD
├── protocolos/
│   ├── protocolo_base.py             # Clase base para protocolos
│   └── modbus/
│       ├── cliente_modbus.py         # Cliente Modbus TCP/RTU
│       ├── servidor_modbus.py        # Servidor Modbus TCP
│       └── manejador_modbus.py       # Coordinador Modbus
├── modelos/
│   ├── dispositivo.py                # Modelo de dispositivos
│   └── sensor.py                     # Modelo de sensores y lecturas
├── base_datos/
│   └── conexion_bd.py                # Gestión de base de datos
├── utilidades/
│   ├── logger.py                     # Sistema de logging
│   ├── validador.py                  # Validación de datos
│   ├── convertidor_datos.py          # Conversión de datos
│   └── constantes.py                 # Constantes del sistema
├── interfaz_web/                     # (Módulo 2)
├── servicios/                        # (Módulo 2)
├── pruebas/                          # (Módulo 4)
├── main.py                           # Punto de entrada principal
├── requirements.txt                  # Dependencias Python
├── configuracion.env                 # Variables de entorno
├── README.md                         # Esta documentación
└── .gitignore                        # Archivos ignorados por Git
```

## 🛠️ Instalación y Configuración

### Prerrequisitos

- **Python 3.10+** (recomendado 3.10.12)
- **Git** para control de versiones
- **Visual Studio Code** (recomendado)
- **PowerShell** (Windows) o terminal (Linux/Mac)

### 1. Crear Estructura del Proyecto

```powershell
# Ejecutar el script de creación de estructura
# (Ver comandos en el artefacto de PowerShell)
```

### 2. Configurar Entorno Virtual

```powershell
# Navegar al directorio del proyecto
cd sistema_bms_demo

# Crear entorno virtual
python -m venv entorno_bms

# Activar entorno virtual (Windows)
.\entorno_bms\Scripts\Activate.ps1

# Activar entorno virtual (Linux/Mac)
source entorno_bms/bin/activate
```

### 3. Instalar Dependencias

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

1. Copiar `configuracion.env` y ajustar según tu entorno
2. Modificar las IPs según tu red:
   - `BMS_IP=192.168.1.95` (IP donde correrá el BMS)
   - `GENETEC_IP=192.168.1.40` (IP del servidor Genetec)

### 5. Ejecutar el Sistema

```powershell
# Ejecutar aplicación principal
python main.py
```

## 🔧 Configuración Avanzada

### Configuración de Red

```env
# IP del sistema BMS
BMS_IP=192.168.1.95
BMS_PUERTO=5000

# IP del servidor Genetec
GENETEC_IP=192.168.1.40
GENETEC_PUERTO=80

# Configuración Modbus
MODBUS_IP=192.168.1.95
MODBUS_PUERTO=502
MODBUS_TIMEOUT=5
MODBUS_INTERVALO_POLLING=5
```

### Configuración de Base de Datos

**SQLite (Por defecto):**
```env
BD_TIPO=sqlite
BD_NOMBRE=bms_demo
BD_RUTA=./base_datos/
```

**PostgreSQL:**
```env
BD_TIPO=postgresql
BD_HOST=localhost
BD_PUERTO=5432
BD_USUARIO=bms_user
BD_PASSWORD=bms_password
BD_NOMBRE=bms_demo
```

### Configuración de Logging

```env
LOG_NIVEL=INFO                                    # DEBUG, INFO, WARNING, ERROR
LOG_ARCHIVO=./logs/bms_sistema.log
LOG_FORMATO=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 🧪 Pruebas y Validación

### Verificar Instalación

```python
# Probar componentes individuales
python -m configuracion.configuracion_general
python -m protocolos.modbus.cliente_modbus
python -m base_datos.conexion_bd
```

### Validar Comunicación Modbus

```python
from protocolos.modbus.cliente_modbus import crear_cliente_modbus

# Crear cliente y probar conexión
cliente = crear_cliente_modbus()
resultado = cliente.conectar()
print(f"Conexión Modbus: {resultado.exitoso}")
```

### Probar Base de Datos

```python
from base_datos.conexion_bd import verificar_bd_disponible, crear_datos_demo

# Verificar BD
if verificar_bd_disponible():
    crear_datos_demo()
    print("Base de datos OK")
```

## 📊 Monitoreo y Estadísticas

El sistema proporciona estadísticas detalladas de:

- **Operaciones Modbus**: Lecturas/escrituras exitosas y fallidas
- **Estado de dispositivos**: Online/offline, tiempos de respuesta
- **Sensores**: Lecturas, alertas, tendencias
- **Sistema**: Memoria, CPU, logs

### Ejemplo de Estadísticas

```json
{
  "modbus": {
    "total_operaciones": 1500,
    "tasa_exito": 98.5,
    "lecturas_exitosas": 1200,
    "escrituras_exitosas": 280,
    "reconexiones": 2
  },
  "dispositivos": {
    "total": 3,
    "online": 3,
    "offline": 0
  },
  "sensores": {
    "total": 2,
    "en_alarma": 0,
    "ultima_lectura": "2024-01-15 14:30:25"
  }
}
```

## 🚨 Solución de Problemas

### Error: "No se puede conectar a Modbus"

1. Verificar que Genetec esté ejecutándose
2. Comprobar IPs en `configuracion.env`
3. Verificar que puerto 502 esté disponible
4. Revisar logs en `./logs/protocolo_modbus.log`

### Error: "Base de datos no disponible"

1. Verificar permisos en directorio `./base_datos/`
2. Comprobar configuración en `configuracion.env`
3. Para PostgreSQL: verificar que el servidor esté ejecutándose

### Error: "Puerto en uso"

1. Cambiar `MODBUS_PUERTO` en configuración
2. Verificar que no haya otra instancia ejecutándose
3. En Linux: `sudo netstat -tulpn | grep :502`

## 🛣️ Roadmap - Próximos Módulos

### 🔄 Módulo 2: Protocolos Adicionales
- **MQTT**: Cliente y broker para IoT
- **BACnet**: Protocolo estándar de automatización
- **SNMP**: Gestión de dispositivos de red
- **HTTP/REST**: API para integraciones externas

### 🌐 Módulo 3: Interfaz Web
- **Dashboard**: Visualización en tiempo real
- **Configuración**: Gestión web de dispositivos
- **Reportes**: Generación de informes
- **API REST**: Interfaz programática completa

### 🧪 Módulo 4: Testing y Optimización
- **Pruebas unitarias**: Cobertura completa
- **Pruebas de integración**: Validación de protocolos
- **Performance**: Optimización y benchmarking
- **Documentación**: Guías completas

## 🤝 Contribución

### Estructura para Nuevos Protocolos

```python
# Ejemplo: protocolos/mqtt/cliente_mqtt.py
from protocolos.protocolo_base import ProtocoloBase

class ClienteMQTT(ProtocoloBase):
    def __init__(self):
        super().__init__("mqtt", config)
    
    def conectar(self) -> ResultadoOperacion:
        # Implementar conexión MQTT
        pass
```

### Convenciones de Código

- **Nomenclatura**: Todo en español (clases, métodos, variables)
- **Documentación**: Docstrings detallados
- **Logging**: Usar el sistema de logging centralizado
- **Validación**: Usar el validador para todos los inputs
- **Configuración**: Variables de entorno para configuración

## 📞 Soporte

Para preguntas o problemas:

1. **Revisar logs** en `./logs/`
2. **Verificar configuración** en `configuracion.env`
3. **Consultar documentación** en `./documentacion/`
4. **Revisar código** - está completamente documentado

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🏆 Estado del Proyecto

### ✅ Módulo 1 - COMPLETADO
- [x] Configuración base
- [x] Protocolo Modbus completo
- [x] Modelos de datos
- [x] Base de datos
- [x] Sistema de logging
- [x] Utilidades completas
- [x] Validación robusta
- [x] Documentación

### 🔄 En Desarrollo
- [ ] Módulo 2: Protocolos adicionales
- [ ] Módulo 3: Interfaz web
- [ ] Módulo 4: Testing

---

**Desarrollado con ❤️ para laboratorios de automatización y sistemas BMS**