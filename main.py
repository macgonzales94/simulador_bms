"""
Aplicación Principal del Sistema BMS Demo - Módulo 1 con Servidor Modbus TCP Real
================================================================================

Versión actualizada que incluye servidor Modbus TCP real usando pymodbus.
El servidor escucha en la IP configurada y expone registros reales del sistema.

Autor: Sistema BMS Demo
Versión: 2.0.0 - Con servidor Modbus TCP real
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes del sistema
from configuracion.configuracion_general import obtener_config, configuracion
from configuracion.configuracion_protocolos import configurador_protocolos
from configuracion.configuracion_base_datos import configurador_bd
from utilidades.logger import obtener_logger_sistema, configurar_nivel_logging

# Importar manejador Modbus V2 con servidor TCP real
from protocolos.modbus.manejador_modbus_v2 import ManejadorModbusV2, ModoOperacionModbus

# Importar modelos
from modelos.dispositivo import Dispositivo, TipoDispositivo, EstadoDispositivo, ConfiguracionDispositivo, ProtocoloComunicacion
from modelos.sensor import crear_sensor_temperatura, crear_sensor_humedad, TipoSensor

class SistemaBMSDemoV2:
    """
    Clase principal del sistema BMS Demo V2 con servidor Modbus TCP real.
    Coordina todos los componentes y servicios incluyendo el servidor TCP.
    """
    
    def __init__(self):
        """Inicializar sistema BMS Demo V2."""
        self.logger = obtener_logger_sistema()
        self.config = obtener_config()
        self.activo = False
        self.manejador_modbus = None
        self.dispositivos_demo = []
        self.sensores_demo = []
        self.tiempo_inicio = datetime.now()
        
        # Control de señales
        signal.signal(signal.SIGINT, self._manejar_senal_salida)
        signal.signal(signal.SIGTERM, self._manejar_senal_salida)
        
        self.logger.info("🚀 Sistema BMS Demo V2 con servidor TCP real inicializado")
        
    def inicializar(self) -> bool:
        """
        Inicializar todos los componentes del sistema.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("🔧 Iniciando inicialización del sistema BMS Demo V2...")
            
            # Mostrar configuración
            self._mostrar_configuracion_sistema()
            
            # Validar configuraciones
            if not self._validar_configuraciones():
                return False
                
            # Crear dispositivos y sensores de demostración
            self._crear_dispositivos_demo()
            
            # Inicializar protocolo Modbus V2 con servidor TCP real
            if not self._inicializar_modbus_v2():
                self.logger.error("❌ No se pudo inicializar Modbus V2")
                return False
                
            # Configurar callbacks y eventos
            self._configurar_callbacks()
            
            self.activo = True
            self.logger.info("✅ Sistema BMS Demo V2 inicializado exitosamente")
            self.logger.info(f"🔥 Servidor Modbus TCP escuchando en {self.config.IP_GENETEC}:{configurador_protocolos.modbus.puerto}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en inicialización: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    def _mostrar_configuracion_sistema(self):
        """Mostrar configuración actual del sistema."""
        self.logger.info("=" * 70)
        self.logger.info("🏗️ CONFIGURACIÓN SISTEMA BMS DEMO V2 - SERVIDOR TCP REAL")
        self.logger.info("=" * 70)
        
        # Configuración general
        self.logger.info(f"📋 Nombre: {self.config.NOMBRE_SISTEMA}")
        self.logger.info(f"📋 Versión: {self.config.VERSION_SISTEMA}")
        self.logger.info(f"🌐 IP BMS: {self.config.IP_BMS}:{self.config.PUERTO_BMS}")
        self.logger.info(f"🌐 IP Genetec: {self.config.IP_GENETEC}:{self.config.PUERTO_GENETEC}")
        self.logger.info(f"🔧 Modo Debug: {self.config.DEBUG}")
        self.logger.info(f"🔧 Entorno: {self.config.ENTORNO}")
        
        # Configuración Modbus específica
        try:
            config_modbus = configurador_protocolos.modbus
            self.logger.info(f"🔌 Modbus TCP IP: {config_modbus.ip}:{config_modbus.puerto}")
            self.logger.info(f"🔌 Modbus Timeout: {config_modbus.timeout}s")
            self.logger.info(f"🔌 Modbus Unit ID: {config_modbus.id_esclavo}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo configuración Modbus: {e}")
        
        # Protocolos habilitados
        try:
            protocolos = configurador_protocolos.obtener_protocolos_habilitados()
            self.logger.info(f"📡 Protocolos habilitados: {[p.value for p in protocolos]}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo protocolos: {e}")
        
        # Base de datos
        try:
            url_bd = configurador_bd.obtener_url_conexion()
            self.logger.info(f"🗄️ Base de datos: {url_bd}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo configuración BD: {e}")
        
        self.logger.info("=" * 70)
        
    def _validar_configuraciones(self) -> bool:
        """Validar que todas las configuraciones sean correctas."""
        try:
            # Validar configuración general
            self.config.validar_configuracion()
            self.logger.info("✅ Configuración general válida")
            
            # Validar configuración de base de datos
            try:
                if not configurador_bd.validar_configuracion():
                    self.logger.error("❌ Configuración de base de datos inválida")
                    return False
                self.logger.info("✅ Configuración de base de datos válida")
            except Exception as e:
                self.logger.warning(f"⚠️ Error validando BD (continuando): {e}")
            
            # Validar protocolos
            try:
                protocolos = configurador_protocolos.obtener_protocolos_habilitados()
                if not protocolos:
                    self.logger.warning("⚠️ No hay protocolos habilitados")
                else:
                    self.logger.info(f"✅ Protocolos válidos: {len(protocolos)}")
            except Exception as e:
                self.logger.warning(f"⚠️ Error validando protocolos: {e}")
                
            # Validar puerto Modbus disponible
            import socket
            try:
                config_modbus = configurador_protocolos.modbus
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((config_modbus.ip, config_modbus.puerto))
                sock.close()
                self.logger.info(f"✅ Puerto Modbus {config_modbus.puerto} disponible")
            except OSError as e:
                self.logger.warning(f"⚠️ Puerto Modbus {config_modbus.puerto} en uso: {e}")
                self.logger.info("ℹ️ El servidor intentará usar el puerto de todas formas")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validando configuraciones: {e}")
            return False
            
    def _crear_dispositivos_demo(self):
        """Crear dispositivos y sensores de demostración."""
        try:
            self.logger.info("🎭 Creando dispositivos de demostración...")
            
            # Dispositivo 1: Cámara IP
            config_camara = ConfiguracionDispositivo(
                ip="192.168.1.101",
                puerto=80,
                protocolo=ProtocoloComunicacion.HTTP,
                timeout=30,
                intervalo_polling=60
            )
            
            camara = Dispositivo(
                nombre="Cámara Lab 01",
                descripcion="Cámara IP en laboratorio - entrada principal",
                tipo=TipoDispositivo.CAMARA.value,
                marca="Axis",
                modelo="P1455-LE",
                direccion_ip="192.168.1.101",
                puerto=80,
                ubicacion_fisica="Laboratorio - Entrada principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True
            )
            camara.configuracion = config_camara
            camara.agregar_etiqueta("seguridad")
            camara.agregar_etiqueta("laboratorio")
            self.dispositivos_demo.append(camara)
            
            # Dispositivo 2: Controlador de puerta
            config_controlador = ConfiguracionDispositivo(
                ip="192.168.1.102",
                puerto=4040,
                protocolo=ProtocoloComunicacion.TCP_IP,
                timeout=15,
                intervalo_polling=30
            )
            
            controlador = Dispositivo(
                nombre="Controlador Puerta Lab",
                descripcion="Controlador Mercury LP1502 - puerta laboratorio",
                tipo=TipoDispositivo.CONTROLADOR.value,
                marca="Mercury",
                modelo="LP1502",
                numero_serie="MC123456789",
                direccion_ip="192.168.1.102",
                puerto=4040,
                ubicacion_fisica="Laboratorio - Puerta principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True
            )
            controlador.configuracion = config_controlador
            controlador.agregar_etiqueta("acceso")
            controlador.agregar_etiqueta("mercury")
            self.dispositivos_demo.append(controlador)
            
            # Dispositivo 3: UPS Mini
            config_ups = ConfiguracionDispositivo(
                ip="192.168.1.103",
                puerto=161,
                protocolo=ProtocoloComunicacion.SNMP,
                timeout=10,
                intervalo_polling=120
            )
            
            ups = Dispositivo(
                nombre="UPS Lab Mini",
                descripcion="UPS para equipos críticos del laboratorio",
                tipo=TipoDispositivo.UPS.value,
                marca="APC",
                modelo="Smart-UPS 750",
                direccion_ip="192.168.1.103",
                puerto=161,
                ubicacion_fisica="Laboratorio - Rack principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True
            )
            ups.configuracion = config_ups
            ups.agregar_etiqueta("energia")
            ups.agregar_etiqueta("critico")
            self.dispositivos_demo.append(ups)
            
            # Crear sensores asociados
            sensor_temp = crear_sensor_temperatura(1, "Sensor Temperatura Lab")
            if sensor_temp.factor_correccion is None:
                sensor_temp.factor_correccion = 1.0
            if sensor_temp.offset_correccion is None:
                sensor_temp.offset_correccion = 0.0
            self.sensores_demo.append(sensor_temp)
            
            sensor_humedad = crear_sensor_humedad(1, "Sensor Humedad Lab")
            if sensor_humedad.factor_correccion is None:
                sensor_humedad.factor_correccion = 1.0
            if sensor_humedad.offset_correccion is None:
                sensor_humedad.offset_correccion = 0.0
            self.sensores_demo.append(sensor_humedad)
            
            self.logger.info(f"✅ Creados {len(self.dispositivos_demo)} dispositivos demo")
            self.logger.info(f"✅ Creados {len(self.sensores_demo)} sensores demo")
            
        except Exception as e:
            self.logger.error(f"❌ Error creando dispositivos demo: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
    def _inicializar_modbus_v2(self) -> bool:
        """Inicializar manejador de protocolo Modbus V2 con servidor TCP real."""
        try:
            self.logger.info("🚀 Inicializando protocolo Modbus V2 con servidor TCP real...")
            
            # Crear manejador en modo servidor TCP (expone servidor real)
            self.manejador_modbus = ManejadorModbusV2(ModoOperacionModbus.SOLO_SERVIDOR_TCP)
            
            # Intentar iniciar
            resultado = self.manejador_modbus.iniciar()
            
            if resultado.exitoso:
                self.logger.info(f"✅ Protocolo Modbus V2 iniciado: {resultado.mensaje}")
                
                # Mostrar información detallada del servidor
                config_modbus = configurador_protocolos.modbus
                self.logger.info("🔥 SERVIDOR MODBUS TCP ACTIVO:")
                self.logger.info(f"   📡 Escuchando en: {config_modbus.ip}:{config_modbus.puerto}")
                self.logger.info(f"   📊 Input Registers: 0-50 (datos del sistema)")
                self.logger.info(f"   ⚙️ Holding Registers: 0-30 (comandos y configuración)")
                self.logger.info(f"   🆔 Unit ID soportado: {config_modbus.id_esclavo}")
                self.logger.info(f"   🔧 Timeout: {config_modbus.timeout}s")
                
                return True
            else:
                self.logger.error(f"❌ Error iniciando Modbus V2: {resultado.mensaje}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Modbus V2: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    def _configurar_callbacks(self):
        """Configurar callbacks y eventos del sistema."""
        try:
            # Callback para datos Modbus (si hay cliente)
            if self.manejador_modbus:
                self.manejador_modbus.agregar_callback_datos(self._callback_datos_modbus)
                self.manejador_modbus.agregar_callback_comando(self._callback_comando_modbus)
                
            self.logger.info("✅ Callbacks configurados")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando callbacks: {e}")
            
    def _callback_datos_modbus(self, datos: Dict[str, Any]):
        """
        Callback para datos recibidos vía Modbus desde Genetec.
        
        Args:
            datos: Datos recibidos del protocolo Modbus
        """
        self.logger.debug(f"📡 Datos Modbus recibidos de Genetec: {datos}")
        
        # Actualizar sensores con datos recibidos
        try:
            for sensor in self.sensores_demo:
                if sensor.tipo_sensor == TipoSensor.TEMPERATURA.value:
                    if 'temperatura' in datos:
                        temperatura = datos['temperatura']
                        if isinstance(temperatura, (int, float)):
                            alertas = sensor.actualizar_valor(temperatura)
                            if alertas:
                                self.logger.warning(f"🚨 Alertas en sensor temperatura: {[a.value for a in alertas]}")
        except Exception as e:
            self.logger.error(f"❌ Error procesando callback Modbus datos: {e}")
            
    def _callback_comando_modbus(self, comando_info: Dict[str, Any]):
        """
        Callback para comandos recibidos vía Modbus desde clientes externos.
        
        Args:
            comando_info: Información del comando recibido
        """
        try:
            accion = comando_info.get('accion', 'desconocida')
            valor = comando_info.get('valor', 0)
            direccion = comando_info.get('direccion', 0)
            
            self.logger.info(f"🔧 Comando Modbus recibido: {accion} (reg:{direccion}, val:{valor})")
            
            # Procesar comandos específicos
            if accion == 'restart':
                self.logger.warning("🔄 Comando RESTART recibido - reiniciando componentes...")
                self._reiniciar_componentes()
            elif accion == 'stop':
                self.logger.warning("⏹️ Comando STOP recibido - iniciando parada del sistema...")
                self.activo = False
            elif accion == 'reset':
                self.logger.info("🔄 Comando RESET recibido - reseteando estadísticas...")
                if self.manejador_modbus:
                    self.manejador_modbus.estadisticas.reset()
                    
        except Exception as e:
            self.logger.error(f"❌ Error procesando callback comando Modbus: {e}")
            
    def _reiniciar_componentes(self):
        """Reiniciar componentes del sistema."""
        try:
            self.logger.info("🔄 Reiniciando componentes del sistema...")
            
            if self.manejador_modbus:
                # Simular reinicio exitoso
                self.manejador_modbus.simular_evento_sistema("reset_alarmas")
                
            self.logger.info("✅ Componentes reiniciados")
            
        except Exception as e:
            self.logger.error(f"❌ Error reiniciando componentes: {e}")
                        
    def ejecutar(self):
        """Ejecutar bucle principal del sistema."""
        try:
            self.logger.info("🚀 Iniciando bucle principal del sistema BMS Demo V2...")
            self.logger.info("📡 Servidor Modbus TCP listo para recibir conexiones")
            
            contador_ciclos = 0
            
            while self.activo:
                contador_ciclos += 1
                
                # Mostrar estado cada 30 segundos (6 ciclos de 5 segundos)
                if contador_ciclos % 6 == 0:
                    self._mostrar_estado_sistema()
                    
                # Simular lecturas de sensores cada 15 segundos (3 ciclos)
                if contador_ciclos % 3 == 0:
                    self._simular_lecturas_sensores()
                    
                # Verificar estado de dispositivos cada minuto (12 ciclos)
                if contador_ciclos % 12 == 0:
                    self._verificar_estado_dispositivos()
                    
                # Simular eventos del sistema ocasionalmente
                if contador_ciclos % 20 == 0:  # Cada 100 segundos
                    self._simular_evento_sistema()
                    
                # Esperar 5 segundos
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Interrupción recibida, deteniendo sistema...")
        except Exception as e:
            self.logger.error(f"❌ Error en bucle principal: {e}")
        finally:
            self.detener()
            
    def _mostrar_estado_sistema(self):
        """Mostrar estado actual del sistema."""
        try:
            self.logger.info("-" * 60)
            self.logger.info("📊 ESTADO ACTUAL DEL SISTEMA BMS V2")
            self.logger.info("-" * 60)
            
            # Estado general
            tiempo_funcionamiento = datetime.now() - self.tiempo_inicio
            self.logger.info(f"⏱️ Tiempo funcionamiento: {tiempo_funcionamiento}")
            
            # Estado dispositivos
            dispositivos_online = len([d for d in self.dispositivos_demo if d.esta_online()])
            self.logger.info(f"📱 Dispositivos: {dispositivos_online}/{len(self.dispositivos_demo)} online")
            
            # Estado sensores
            sensores_alarma = len([s for s in self.sensores_demo if s.esta_en_alarma()])
            self.logger.info(f"🌡️ Sensores: {len(self.sensores_demo)} total, {sensores_alarma} en alarma")
            
            # Estado Modbus V2
            if self.manejador_modbus:
                try:
                    estado_modbus = self.manejador_modbus.obtener_estado_completo()
                    servidor_tcp = estado_modbus.get('servidor_tcp', {})
                    stats = estado_modbus.get('estadisticas', {})
                    
                    self.logger.info(f"🔌 Modbus TCP: {estado_modbus['modo_operacion']} - Activo: {estado_modbus['activo']}")
                    self.logger.info(f"   📡 Servidor escuchando: {servidor_tcp.get('escuchando', False)} en {servidor_tcp.get('ip', 'N/A')}:{servidor_tcp.get('puerto', 'N/A')}")
                    self.logger.info(f"   📊 Operaciones: {stats.get('total_operaciones', 0)} (éxito: {stats.get('tasa_exito', 0)}%)")
                    self.logger.info(f"   🔧 Comandos recibidos: {stats.get('comandos_recibidos', 0)}")
                    
                    # Mostrar datos actuales del sistema
                    datos_sistema = estado_modbus.get('datos_sistema', {})
                    self.logger.info(f"   🌡️ Temperatura: {datos_sistema.get('temperatura_lab', 0):.1f}°C")
                    self.logger.info(f"   💧 Humedad: {datos_sistema.get('humedad_lab', 0):.0f}%")
                    self.logger.info(f"   🚨 Alarmas: {datos_sistema.get('alarmas_activas', 0)}")
                    
                except Exception as e:
                    self.logger.debug(f"Error obteniendo estado Modbus: {e}")
                    
            self.logger.info("-" * 60)
            
        except Exception as e:
            self.logger.error(f"❌ Error mostrando estado: {e}")
            
    def _simular_lecturas_sensores(self):
        """Simular lecturas de sensores para demostración."""
        try:
            import random
            
            for sensor in self.sensores_demo:
                try:
                    if sensor.tipo_sensor == TipoSensor.TEMPERATURA.value:
                        # Simular temperatura entre 20-30°C con variación
                        temperatura = 25 + random.uniform(-5, 5)
                        alertas = sensor.actualizar_valor(temperatura)
                        
                        # Actualizar en el manejador Modbus para que se refleje en los registros
                        if self.manejador_modbus:
                            self.manejador_modbus.datos_sistema['temperatura_lab'] = temperatura
                        
                        if alertas:
                            self.logger.warning(f"🚨 Alertas temperatura: {[a.value for a in alertas]} - Valor: {temperatura:.1f}°C")
                        else:
                            self.logger.debug(f"🌡️ Temperatura actualizada: {temperatura:.1f}°C")
                            
                    elif sensor.tipo_sensor == TipoSensor.HUMEDAD.value:
                        # Simular humedad entre 40-70%
                        humedad = 55 + random.uniform(-15, 15)
                        alertas = sensor.actualizar_valor(humedad)
                        
                        # Actualizar en el manejador Modbus
                        if self.manejador_modbus:
                            self.manejador_modbus.datos_sistema['humedad_lab'] = humedad
                        
                        if alertas:
                            self.logger.warning(f"🚨 Alertas humedad: {[a.value for a in alertas]} - Valor: {humedad:.0f}%")
                        else:
                            self.logger.debug(f"💧 Humedad actualizada: {humedad:.0f}%")
                            
                except Exception as e:
                    self.logger.error(f"❌ Error actualizando sensor {sensor.tipo_sensor}: {e}")
                        
        except Exception as e:
            self.logger.error(f"❌ Error simulando lecturas: {e}")
            
    def _verificar_estado_dispositivos(self):
        """Verificar estado de todos los dispositivos."""
        try:
            for dispositivo in self.dispositivos_demo:
                # Simular verificación de conectividad (90% probabilidad online)
                import random
                if random.random() > 0.1:
                    if not dispositivo.esta_online():
                        dispositivo.actualizar_estado(EstadoDispositivo.ONLINE, random.uniform(0.1, 2.0))
                        self.logger.info(f"✅ Dispositivo {dispositivo.nombre} volvió online")
                else:
                    if dispositivo.esta_online():
                        dispositivo.actualizar_estado(EstadoDispositivo.OFFLINE)
                        self.logger.warning(f"⚠️ Dispositivo {dispositivo.nombre} se desconectó")
                        
            # Actualizar contadores en el manejador Modbus
            if self.manejador_modbus:
                dispositivos_online = len([d for d in self.dispositivos_demo if d.esta_online()])
                self.manejador_modbus.datos_sistema['camaras_online'] = len([d for d in self.dispositivos_demo if d.tipo == TipoDispositivo.CAMARA.value and d.esta_online()])
                self.manejador_modbus.datos_sistema['controladores_online'] = len([d for d in self.dispositivos_demo if d.tipo == TipoDispositivo.CONTROLADOR.value and d.esta_online()])
                        
        except Exception as e:
            self.logger.error(f"❌ Error verificando dispositivos: {e}")
            
    def _simular_evento_sistema(self):
        """Simular eventos del sistema ocasionalmente."""
        try:
            import random
            
            eventos = ['normal', 'alarma_temperatura', 'dispositivo_offline', 'reset_alarmas']
            evento = random.choice(eventos)
            
            if evento == 'alarma_temperatura' and self.manejador_modbus:
                self.logger.warning("🚨 Simulando alarma de temperatura alta...")
                self.manejador_modbus.simular_evento_sistema("alarma_temperatura", {"temperatura": 35.0})
                
            elif evento == 'dispositivo_offline' and self.manejador_modbus:
                dispositivo_tipo = random.choice(['camara', 'controlador'])
                self.logger.warning(f"📴 Simulando dispositivo {dispositivo_tipo} offline...")
                self.manejador_modbus.simular_evento_sistema("dispositivo_offline", {"dispositivo": dispositivo_tipo})
                
            elif evento == 'reset_alarmas' and self.manejador_modbus:
                self.logger.info("✅ Simulando reset de alarmas...")
                self.manejador_modbus.simular_evento_sistema("reset_alarmas")
                
        except Exception as e:
            self.logger.error(f"❌ Error simulando evento: {e}")
            
    def _manejar_senal_salida(self, signum, frame):
        """Manejar señales de salida del sistema."""
        self.logger.info(f"⏹️ Señal recibida: {signum}, iniciando parada del sistema...")
        self.activo = False
        
    def detener(self):
        """Detener sistema y limpiar recursos."""
        try:
            self.logger.info("⏹️ Deteniendo sistema BMS Demo V2...")
            
            self.activo = False
            
            # Detener protocolo Modbus V2
            if self.manejador_modbus:
                try:
                    resultado = self.manejador_modbus.detener()
                    self.logger.info(f"🔌 Modbus V2 detenido: {resultado.mensaje}")
                except Exception as e:
                    self.logger.error(f"❌ Error deteniendo Modbus V2: {e}")
                
            # Limpiar recursos
            self.dispositivos_demo.clear()
            self.sensores_demo.clear()
            
            self.logger.info("✅ Sistema BMS Demo V2 detenido completamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo sistema: {e}")

def main():
    """Función principal del sistema BMS Demo V2."""
    print("=" * 70)
    print("🚀 SISTEMA BMS DEMO V2 - SERVIDOR MODBUS TCP REAL")
    print("Configuración base + Servidor Modbus TCP + Modelos")
    print("=" * 70)
    
    # Crear e inicializar sistema
    sistema = SistemaBMSDemoV2()
    
    if sistema.inicializar():
        print("✅ Sistema inicializado correctamente")
        print("🔥 Servidor Modbus TCP activo y escuchando")
        print("📡 Conecta desde cualquier cliente Modbus a la IP configurada")
        print("⏹️ Presiona Ctrl+C para detener el sistema")
        print("-" * 70)
        
        # Ejecutar sistema
        sistema.ejecutar()
    else:
        print("❌ Error inicializando sistema")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)