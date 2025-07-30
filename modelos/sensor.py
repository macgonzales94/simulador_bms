"""
Modelo de Sensor para Sistema BMS
=================================

Este módulo define las clases para sensores y lecturas de sensores,
incluyendo validaciones, rangos y alertas específicas para cada tipo de sensor.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Importar modelo base
from modelos.dispositivo import Base, Dispositivo, TipoDispositivo

class TipoSensor(Enum):
    """Tipos específicos de sensores soportados."""
    TEMPERATURA = "temperatura"
    HUMEDAD = "humedad"
    PRESION = "presion"
    LUMINOSIDAD = "luminosidad"
    MOVIMIENTO = "movimiento"
    PUERTA = "puerta"
    HUMO = "humo"
    GASES = "gases"
    VIBRATION = "vibracion"
    NIVEL_AGUA = "nivel_agua"
    CORRIENTE = "corriente"
    VOLTAJE = "voltaje"
    ENERGIA = "energia"
    FLUJO = "flujo"
    PH = "ph"
    CONDUCTIVIDAD = "conductividad"

class UnidadMedida(Enum):
    """Unidades de medida para sensores."""
    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    KELVIN = "K"
    PORCENTAJE = "%"
    PASCAL = "Pa"
    BAR = "bar"
    MBAR = "mbar"
    LUX = "lux"
    VOLTIOS = "V"
    AMPERIOS = "A"
    WATTS = "W"
    KILOWATTS = "kW"
    METRO = "m"
    CENTIMETRO = "cm"
    LITRO = "L"
    METRO_CUBICO = "m³"
    PPM = "ppm"
    DB = "dB"
    BINARIO = "0/1"
    SIN_UNIDAD = ""

class TipoAlerta(Enum):
    """Tipos de alertas de sensores."""
    VALOR_ALTO = "valor_alto"
    VALOR_BAJO = "valor_bajo"
    VALOR_CRITICO_ALTO = "valor_critico_alto"
    VALOR_CRITICO_BAJO = "valor_critico_bajo"
    SIN_LECTURA = "sin_lectura"
    ERROR_SENSOR = "error_sensor"
    CAMBIO_BRUSCO = "cambio_brusco"

@dataclass
class RangoSensor:
    """Definición de rangos y límites para un sensor."""
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    critico_bajo: Optional[float] = None
    critico_alto: Optional[float] = None
    alerta_bajo: Optional[float] = None
    alerta_alto: Optional[float] = None
    precision: int = 2
    
    def validar_valor(self, valor: float) -> List[TipoAlerta]:
        """
        Validar un valor contra los rangos definidos.
        
        Args:
            valor: Valor a validar
            
        Returns:
            Lista de alertas generadas
        """
        alertas = []
        
        if self.critico_alto is not None and valor > self.critico_alto:
            alertas.append(TipoAlerta.VALOR_CRITICO_ALTO)
        elif self.alerta_alto is not None and valor > self.alerta_alto:
            alertas.append(TipoAlerta.VALOR_ALTO)
            
        if self.critico_bajo is not None and valor < self.critico_bajo:
            alertas.append(TipoAlerta.VALOR_CRITICO_BAJO)
        elif self.alerta_bajo is not None and valor < self.alerta_bajo:
            alertas.append(TipoAlerta.VALOR_BAJO)
            
        return alertas
        
    def esta_en_rango_normal(self, valor: float) -> bool:
        """Verificar si el valor está en rango normal."""
        alertas = self.validar_valor(valor)
        return len(alertas) == 0
        
    def formatear_valor(self, valor: float) -> float:
        """Formatear valor según la precisión definida."""
        return round(valor, self.precision)

class Sensor(Base):
    """
    Modelo de sensor que extiende el concepto de dispositivo
    con capacidades específicas de medición y monitoreo.
    """
    
    __tablename__ = 'sensores'
    
    # Campos principales
    id = Column(Integer, primary_key=True, autoincrement=True)
    dispositivo_id = Column(Integer, ForeignKey('dispositivos.id'), nullable=False)
    
    # Información del sensor
    tipo_sensor = Column(String(50), nullable=False, index=True)
    unidad_medida = Column(String(10), nullable=False)
    precision = Column(Integer, default=2)
    
    # Valor actual
    valor_actual = Column(Float)
    valor_anterior = Column(Float)
    timestamp_lectura = Column(DateTime)
    
    # Rangos y límites (almacenados como JSON)
    rango_minimo = Column(Float)
    rango_maximo = Column(Float)
    limite_critico_bajo = Column(Float)
    limite_critico_alto = Column(Float)
    limite_alerta_bajo = Column(Float)
    limite_alerta_alto = Column(Float)
    
    # Estado del sensor
    activo = Column(Boolean, default=True, nullable=False)
    calibrado = Column(Boolean, default=False, nullable=False)
    fecha_calibracion = Column(DateTime)
    intervalo_lectura = Column(Integer, default=60)  # segundos
    
    # Configuración específica
    factor_correccion = Column(Float, default=1.0)
    offset_correccion = Column(Float, default=0.0)
    filtro_habilitado = Column(Boolean, default=False)
    filtro_tipo = Column(String(20))  # media_movil, mediana, etc.
    filtro_ventana = Column(Integer, default=5)
    
    # Alertas
    alertas_habilitadas = Column(Boolean, default=True, nullable=False)
    nivel_alerta_actual = Column(String(20))
    ultima_alerta = Column(DateTime)
    
    # Metadatos
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación con dispositivo
    dispositivo = relationship("Dispositivo", backref="sensores")
    
    def __init__(self, **kwargs):
        """Inicializar sensor."""
        super().__init__(**kwargs)
        self._rango_obj = None
        self._historial_valores = []
        
    @property
    def rango(self) -> RangoSensor:
        """Obtener rango como objeto."""
        if self._rango_obj is None:
            self._rango_obj = RangoSensor(
                minimo=self.rango_minimo,
                maximo=self.rango_maximo,
                critico_bajo=self.limite_critico_bajo,
                critico_alto=self.limite_critico_alto,
                alerta_bajo=self.limite_alerta_bajo,
                alerta_alto=self.limite_alerta_alto,
                precision=self.precision
            )
        return self._rango_obj
        
    @rango.setter
    def rango(self, rango: RangoSensor):
        """Establecer rango desde objeto."""
        self._rango_obj = rango
        self.rango_minimo = rango.minimo
        self.rango_maximo = rango.maximo
        self.limite_critico_bajo = rango.critico_bajo
        self.limite_critico_alto = rango.critico_alto
        self.limite_alerta_bajo = rango.alerta_bajo
        self.limite_alerta_alto = rango.alerta_alto
        self.precision = rango.precision
        
    def actualizar_valor(self, nuevo_valor: float, timestamp: datetime = None) -> List[TipoAlerta]:
        """
        Actualizar valor del sensor y detectar alertas.
        
        Args:
            nuevo_valor: Nuevo valor leído
            timestamp: Timestamp de la lectura (opcional)
            
        Returns:
            Lista de alertas generadas
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Aplicar correcciones
        valor_corregido = (nuevo_valor * self.factor_correccion) + self.offset_correccion
        
        # Aplicar filtros si están habilitados
        if self.filtro_habilitado:
            valor_corregido = self._aplicar_filtro(valor_corregido)
            
        # Guardar valores anteriores
        self.valor_anterior = self.valor_actual
        self.valor_actual = self.rango.formatear_valor(valor_corregido)
        self.timestamp_lectura = timestamp
        
        # Agregar al historial temporal
        self._historial_valores.append({
            'valor': self.valor_actual,
            'timestamp': timestamp
        })
        
        # Mantener solo los últimos 100 valores en memoria
        if len(self._historial_valores) > 100:
            self._historial_valores = self._historial_valores[-100:]
            
        # Detectar alertas
        alertas = []
        if self.alertas_habilitadas:
            alertas = self.rango.validar_valor(self.valor_actual)
            
            # Verificar cambio brusco
            if self.valor_anterior is not None:
                cambio_porcentual = abs(self.valor_actual - self.valor_anterior)
                if self.valor_anterior != 0:
                    cambio_porcentual = (cambio_porcentual / abs(self.valor_anterior)) * 100
                    
                # Si el cambio es mayor al 50%, es un cambio brusco
                if cambio_porcentual > 50:
                    alertas.append(TipoAlerta.CAMBIO_BRUSCO)
                    
            # Actualizar nivel de alerta
            if alertas:
                # Tomar la alerta más severa
                orden_severidad = [
                    TipoAlerta.VALOR_CRITICO_ALTO,
                    TipoAlerta.VALOR_CRITICO_BAJO,
                    TipoAlerta.VALOR_ALTO,
                    TipoAlerta.VALOR_BAJO,
                    TipoAlerta.CAMBIO_BRUSCO
                ]
                
                for tipo_alerta in orden_severidad:
                    if tipo_alerta in alertas:
                        self.nivel_alerta_actual = tipo_alerta.value
                        self.ultima_alerta = timestamp
                        break
            else:
                self.nivel_alerta_actual = None
                
        return alertas
        
    def _aplicar_filtro(self, valor: float) -> float:
        """Aplicar filtro al valor según configuración."""
        if not self._historial_valores or len(self._historial_valores) < 2:
            return valor
            
        if self.filtro_tipo == "media_movil":
            # Media móvil de los últimos N valores
            ultimos_valores = [v['valor'] for v in self._historial_valores[-self.filtro_ventana:]]
            ultimos_valores.append(valor)
            return sum(ultimos_valores) / len(ultimos_valores)
            
        elif self.filtro_tipo == "mediana":
            # Mediana de los últimos N valores
            ultimos_valores = [v['valor'] for v in self._historial_valores[-self.filtro_ventana:]]
            ultimos_valores.append(valor)
            ultimos_valores.sort()
            n = len(ultimos_valores)
            if n % 2 == 0:
                return (ultimos_valores[n//2 - 1] + ultimos_valores[n//2]) / 2
            else:
                return ultimos_valores[n//2]
                
        return valor
        
    def obtener_tendencia(self, ventana_minutos: int = 30) -> Optional[str]:
        """
        Obtener tendencia del sensor en ventana de tiempo.
        
        Args:
            ventana_minutos: Ventana de tiempo en minutos
            
        Returns:
            'subiendo', 'bajando', 'estable' o None
        """
        if not self._historial_valores or len(self._historial_valores) < 3:
            return None
            
        tiempo_limite = datetime.now() - timedelta(minutes=ventana_minutos)
        valores_ventana = [
            v for v in self._historial_valores 
            if v['timestamp'] >= tiempo_limite
        ]
        
        if len(valores_ventana) < 3:
            return None
            
        # Calcular tendencia usando regresión lineal simple
        n = len(valores_ventana)
        sum_x = sum(range(n))
        sum_y = sum(v['valor'] for v in valores_ventana)
        sum_xy = sum(i * v['valor'] for i, v in enumerate(valores_ventana))
        sum_x2 = sum(i * i for i in range(n))
        
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determinar tendencia basada en la pendiente
        if abs(pendiente) < 0.1:  # Umbral de estabilidad
            return "estable"
        elif pendiente > 0:
            return "subiendo"
        else:
            return "bajando"
            
    def esta_en_alarma(self) -> bool:
        """Verificar si el sensor está en estado de alarma."""
        return self.nivel_alerta_actual in [
            TipoAlerta.VALOR_CRITICO_ALTO.value,
            TipoAlerta.VALOR_CRITICO_BAJO.value
        ]
        
    def tiempo_desde_ultima_lectura(self) -> Optional[float]:
        """Obtener tiempo transcurrido desde la última lectura en segundos."""
        if self.timestamp_lectura:
            delta = datetime.now() - self.timestamp_lectura
            return delta.total_seconds()
        return None
        
    def requiere_calibracion(self) -> bool:
        """Verificar si el sensor requiere calibración."""
        if not self.calibrado:
            return True
            
        if self.fecha_calibracion:
            # Requiere calibración si han pasado más de 6 meses
            tiempo_calibracion = datetime.now() - self.fecha_calibracion
            return tiempo_calibracion.days > 180
            
        return True
        
    def marcar_calibrado(self):
        """Marcar sensor como calibrado."""
        self.calibrado = True
        self.fecha_calibracion = datetime.now()
        
    def obtener_estadisticas(self, ventana_horas: int = 24) -> Dict[str, Any]:
        """
        Obtener estadísticas del sensor en ventana de tiempo.
        
        Args:
            ventana_horas: Ventana de tiempo en horas
            
        Returns:
            Diccionario con estadísticas
        """
        tiempo_limite = datetime.now() - timedelta(hours=ventana_horas)
        valores_ventana = [
            v['valor'] for v in self._historial_valores 
            if v['timestamp'] >= tiempo_limite
        ]
        
        if not valores_ventana:
            return {
                'lecturas': 0,
                'valor_promedio': None,
                'valor_minimo': None,
                'valor_maximo': None,
                'desviacion_estandar': None
            }
            
        promedio = sum(valores_ventana) / len(valores_ventana)
        minimo = min(valores_ventana)
        maximo = max(valores_ventana)
        
        # Calcular desviación estándar
        if len(valores_ventana) > 1:
            varianza = sum((x - promedio) ** 2 for x in valores_ventana) / len(valores_ventana)
            desviacion = varianza ** 0.5
        else:
            desviacion = 0
            
        return {
            'lecturas': len(valores_ventana),
            'valor_promedio': round(promedio, self.precision),
            'valor_minimo': minimo,
            'valor_maximo': maximo,
            'desviacion_estandar': round(desviacion, self.precision),
            'tendencia': self.obtener_tendencia(),
            'tiempo_desde_ultima_lectura': self.tiempo_desde_ultima_lectura()
        }
        
    def to_dict(self, incluir_historial: bool = False) -> Dict[str, Any]:
        """
        Convertir sensor a diccionario.
        
        Args:
            incluir_historial: Si incluir historial de valores
            
        Returns:
            Diccionario con datos del sensor
        """
        resultado = {
            'id': self.id,
            'dispositivo_id': self.dispositivo_id,
            'tipo_sensor': self.tipo_sensor,
            'unidad_medida': self.unidad_medida,
            'valor_actual': self.valor_actual,
            'valor_anterior': self.valor_anterior,
            'timestamp_lectura': self.timestamp_lectura.isoformat() if self.timestamp_lectura else None,
            'activo': self.activo,
            'calibrado': self.calibrado,
            'fecha_calibracion': self.fecha_calibracion.isoformat() if self.fecha_calibracion else None,
            'intervalo_lectura': self.intervalo_lectura,
            'alertas_habilitadas': self.alertas_habilitadas,
            'nivel_alerta_actual': self.nivel_alerta_actual,
            'ultima_alerta': self.ultima_alerta.isoformat() if self.ultima_alerta else None,
            'esta_en_alarma': self.esta_en_alarma(),
            'requiere_calibracion': self.requiere_calibracion(),
            'tiempo_desde_ultima_lectura': self.tiempo_desde_ultima_lectura(),
            'estadisticas_24h': self.obtener_estadisticas(24),
            'rango': {
                'minimo': self.rango_minimo,
                'maximo': self.rango_maximo,
                'critico_bajo': self.limite_critico_bajo,
                'critico_alto': self.limite_critico_alto,
                'alerta_bajo': self.limite_alerta_bajo,
                'alerta_alto': self.limite_alerta_alto
            }
        }
        
        if incluir_historial:
            resultado['historial_valores'] = [
                {
                    'valor': v['valor'],
                    'timestamp': v['timestamp'].isoformat()
                }
                for v in self._historial_valores[-50:]  # Últimos 50 valores
            ]
            
        return resultado
        
    def __repr__(self):
        """Representación string del sensor."""
        return f"<Sensor(id={self.id}, tipo='{self.tipo_sensor}', valor={self.valor_actual} {self.unidad_medida})>"

class LecturaSensor(Base):
    """
    Modelo para almacenar lecturas históricas de sensores.
    Permite mantener un historial persistente de todas las lecturas.
    """
    
    __tablename__ = 'lecturas_sensores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey('sensores.id'), nullable=False, index=True)
    valor = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Metadatos de la lectura
    calidad = Column(String(20), default='buena')  # buena, regular, mala
    fuente = Column(String(50))  # modbus, mqtt, http, etc.
    procesada = Column(Boolean, default=False, nullable=False)
    
    # Relación con sensor
    sensor = relationship("Sensor", backref="lecturas_historicas")
    
    def __repr__(self):
        """Representación string de la lectura."""
        return f"<LecturaSensor(sensor_id={self.sensor_id}, valor={self.valor}, timestamp={self.timestamp})>"

# Funciones de utilidad
def crear_sensor_temperatura(dispositivo_id: int, nombre: str = "Sensor Temperatura") -> Sensor:
    """Crear sensor de temperatura con configuración estándar."""
    rango = RangoSensor(
        minimo=-10.0,
        maximo=50.0,
        critico_bajo=0.0,
        critico_alto=40.0,
        alerta_bajo=5.0,
        alerta_alto=35.0,
        precision=1
    )
    
    sensor = Sensor(
        dispositivo_id=dispositivo_id,
        tipo_sensor=TipoSensor.TEMPERATURA.value,
        unidad_medida=UnidadMedida.CELSIUS.value,
        precision=1,
        intervalo_lectura=60,
        alertas_habilitadas=True
    )
    
    sensor.rango = rango
    return sensor

def crear_sensor_humedad(dispositivo_id: int, nombre: str = "Sensor Humedad") -> Sensor:
    """Crear sensor de humedad con configuración estándar."""
    rango = RangoSensor(
        minimo=0.0,
        maximo=100.0,
        critico_bajo=20.0,
        critico_alto=80.0,
        alerta_bajo=30.0,
        alerta_alto=70.0,
        precision=0
    )
    
    sensor = Sensor(
        dispositivo_id=dispositivo_id,
        tipo_sensor=TipoSensor.HUMEDAD.value,
        unidad_medida=UnidadMedida.PORCENTAJE.value,
        precision=0,
        intervalo_lectura=60,
        alertas_habilitadas=True
    )
    
    sensor.rango = rango
    return sensor

def obtener_sensores_en_alarma(sensores: List[Sensor]) -> List[Sensor]:
    """Obtener sensores que están en estado de alarma."""
    return [s for s in sensores if s.esta_en_alarma()]

def obtener_sensores_sin_lectura(sensores: List[Sensor], minutos_limite: int = 10) -> List[Sensor]:
    """Obtener sensores que no tienen lecturas recientes."""
    limite_tiempo = timedelta(minutes=minutos_limite)
    sensores_sin_lectura = []
    
    for sensor in sensores:
        tiempo_sin_lectura = sensor.tiempo_desde_ultima_lectura()
        if tiempo_sin_lectura is None or tiempo_sin_lectura > limite_tiempo.total_seconds():
            sensores_sin_lectura.append(sensor)
            
    return sensores_sin_lectura

if __name__ == "__main__":
    # Prueba del modelo de sensor
    print("Probando modelo de sensor...")
    
    # Crear sensor de temperatura
    sensor_temp = crear_sensor_temperatura(1, "Sensor Temperatura Lab")
    
    # Simular lecturas
    import random
    for i in range(10):
        temperatura = 20 + random.uniform(-5, 15)
        alertas = sensor_temp.actualizar_valor(temperatura)
        
        print(f"Lectura {i+1}: {temperatura:.1f}°C")
        if alertas:
            print(f"  Alertas: {[a.value for a in alertas]}")
            
    # Obtener estadísticas
    stats = sensor_temp.obtener_estadisticas()
    print(f"\nEstadísticas del sensor:")
    print(f"  Lecturas: {stats['lecturas']}")
    print(f"  Promedio: {stats['valor_promedio']}°C")
    print(f"  Rango: {stats['valor_minimo']} - {stats['valor_maximo']}°C")
    print(f"  Tendencia: {stats['tendencia']}")
    
    # Verificar estado
    print(f"\nEstado del sensor:")
    print(f"  En alarma: {sensor_temp.esta_en_alarma()}")
    print(f"  Requiere calibración: {sensor_temp.requiere_calibracion()}")
    print(f"  Nivel alerta actual: {sensor_temp.nivel_alerta_actual}")
    
    print("✓ Prueba de modelo de sensor completada")