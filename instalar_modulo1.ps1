# ============================================================================
# SCRIPT DE INSTALACIÓN AUTOMÁTICA - MÓDULO 1 BMS DEMO
# Script PowerShell para instalar y configurar automáticamente el Módulo 1
# ============================================================================

param(
    [switch]$SkipVenv,           # Saltar creación de entorno virtual
    [switch]$SkipDependencies,   # Saltar instalación de dependencias
    [switch]$RunTests,           # Ejecutar pruebas al final
    [switch]$Help                # Mostrar ayuda
)

# Colores para output
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-ColorOutput "===========================================================================" $ColorInfo
    Write-ColorOutput "INSTALADOR AUTOMÁTICO - SISTEMA BMS DEMO MÓDULO 1" $ColorInfo
    Write-ColorOutput "===========================================================================" $ColorInfo
    Write-Host ""
    Write-ColorOutput "DESCRIPCIÓN:" $ColorInfo
    Write-Host "  Este script automatiza la instalación completa del Módulo 1 del Sistema BMS Demo"
    Write-Host "  incluyendo estructura de directorios, entorno virtual, dependencias y validación."
    Write-Host ""
    Write-ColorOutput "USO:" $ColorInfo
    Write-Host "  .\instalar_modulo1.ps1 [opciones]"
    Write-Host ""
    Write-ColorOutput "OPCIONES:" $ColorInfo
    Write-Host "  -SkipVenv            Saltar creación de entorno virtual"
    Write-Host "  -SkipDependencies    Saltar instalación de dependencias"
    Write-Host "  -RunTests            Ejecutar pruebas automáticamente al final"
    Write-Host "  -Help                Mostrar esta ayuda"
    Write-Host ""
    Write-ColorOutput "EJEMPLOS:" $ColorInfo
    Write-Host "  .\instalar_modulo1.ps1                    # Instalación completa"
    Write-Host "  .\instalar_modulo1.ps1 -RunTests          # Instalación + pruebas"
    Write-Host "  .\instalar_modulo1.ps1 -SkipVenv          # Solo dependencias (venv existente)"
    Write-Host ""
    Write-ColorOutput "REQUISITOS:" $ColorInfo
    Write-Host "  - Python 3.10 o superior"
    Write-Host "  - PowerShell 5.0 o superior"
    Write-Host "  - Permisos de ejecución de scripts"
    Write-Host ""
    Write-ColorOutput "===========================================================================" $ColorInfo
}

function Test-PythonInstallation {
    Write-ColorOutput "🔍 Verificando instalación de Python..." $ColorInfo
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python no encontrado"
        }
        
        # Verificar versión mínima (3.10)
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
                throw "Python 3.10+ requerido, encontrado: $pythonVersion"
            }
        }
        
        Write-ColorOutput "✅ Python encontrado: $pythonVersion" $ColorSuccess
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error: $($_.Exception.Message)" $ColorError
        Write-ColorOutput "💡 Instalar Python 3.10+ desde: https://www.python.org/downloads/" $ColorWarning
        return $false
    }
}

function Test-ExecutionPolicy {
    Write-ColorOutput "🔍 Verificando política de ejecución..." $ColorInfo
    
    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -eq "Restricted") {
        Write-ColorOutput "⚠️  Política de ejecución restrictiva detectada" $ColorWarning
        Write-ColorOutput "🔧 Cambiando política de ejecución..." $ColorInfo
        
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-ColorOutput "✅ Política de ejecución actualizada" $ColorSuccess
        }
        catch {
            Write-ColorOutput "❌ Error cambiando política de ejecución: $($_.Exception.Message)" $ColorError
            return $false
        }
    }
    else {
        Write-ColorOutput "✅ Política de ejecución OK: $policy" $ColorSuccess
    }
    return $true
}

function Test-ProjectStructure {
    Write-ColorOutput "🔍 Verificando estructura del proyecto..." $ColorInfo
    
    $requiredDirs = @(
        "configuracion", "protocolos", "modelos", "base_datos", 
        "utilidades", "servicios", "interfaz_web", "pruebas"
    )
    
    $requiredFiles = @(
        "main.py", "requirements.txt", "configuracion.env", "README.md"
    )
    
    $missing = @()
    
    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            $missing += "Directorio: $dir"
        }
    }
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missing += "Archivo: $file"
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-ColorOutput "❌ Estructura incompleta. Faltantes:" $ColorError
        foreach ($item in $missing) {
            Write-ColorOutput "   - $item" $ColorError
        }
        Write-ColorOutput "💡 Ejecutar primero el script de creación de estructura" $ColorWarning
        return $false
    }
    
    Write-ColorOutput "✅ Estructura del proyecto completa" $ColorSuccess
    return $true
}

function New-VirtualEnvironment {
    if ($SkipVenv) {
        Write-ColorOutput "⏭️  Saltando creación de entorno virtual" $ColorWarning
        return $true
    }
    
    Write-ColorOutput "🐍 Creando entorno virtual..." $ColorInfo
    
    # Eliminar entorno existente si existe
    if (Test-Path "entorno_bms") {
        Write-ColorOutput "🗑️  Eliminando entorno virtual existente..." $ColorWarning
        Remove-Item -Recurse -Force "entorno_bms" -ErrorAction SilentlyContinue
    }
    
    try {
        # Crear entorno virtual
        python -m venv entorno_bms
        if ($LASTEXITCODE -ne 0) {
            throw "Error creando entorno virtual"
        }
        
        Write-ColorOutput "✅ Entorno virtual creado: entorno_bms" $ColorSuccess
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error creando entorno virtual: $($_.Exception.Message)" $ColorError
        return $false
    }
}

function Enable-VirtualEnvironment {
    if ($SkipVenv) {
        Write-ColorOutput "⏭️  Usando entorno Python del sistema" $ColorWarning
        return $true
    }
    
    Write-ColorOutput "🔌 Activando entorno virtual..." $ColorInfo
    
    $activateScript = ".\entorno_bms\Scripts\Activate.ps1"
    
    if (-not (Test-Path $activateScript)) {
        Write-ColorOutput "❌ Script de activación no encontrado: $activateScript" $ColorError
        return $false
    }
    
    try {
        & $activateScript
        Write-ColorOutput "✅ Entorno virtual activado" $ColorSuccess
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error activando entorno virtual: $($_.Exception.Message)" $ColorError
        return $false
    }
}

function Install-Dependencies {
    if ($SkipDependencies) {
        Write-ColorOutput "⏭️  Saltando instalación de dependencias" $ColorWarning
        return $true
    }
    
    Write-ColorOutput "📦 Instalando dependencias..." $ColorInfo
    
    try {
        # Actualizar pip
        Write-ColorOutput "⬆️  Actualizando pip..." $ColorInfo
        python -m pip install --upgrade pip --quiet
        
        # Instalar dependencias básicas primero
        Write-ColorOutput "📋 Instalando dependencias básicas..." $ColorInfo
        $basicDeps = @(
            "python-dotenv==1.0.0",
            "SQLAlchemy==2.0.20", 
            "colorlog==6.7.0",
            "psutil==5.9.5"
        )
        
        foreach ($dep in $basicDeps) {
            Write-Host "   - Instalando $dep" -ForegroundColor Gray
            python -m pip install $dep --quiet
            if ($LASTEXITCODE -ne 0) {
                throw "Error instalando $dep"
            }
        }
        
        # Instalar Modbus
        Write-ColorOutput "🔌 Instalando PyModbus..." $ColorInfo
        python -m pip install pymodbus==3.4.1 --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Error instalando PyModbus"
        }
        
        # Instalar Flask (para futuros módulos)
        Write-ColorOutput "🌐 Instalando Flask..." $ColorInfo
        python -m pip install Flask==2.3.3 Flask-CORS==4.0.0 Flask-SQLAlchemy==3.0.5 --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Error instalando Flask"
        }
        
        # Instalar herramientas de desarrollo
        Write-ColorOutput "🛠️  Instalando herramientas de desarrollo..." $ColorInfo
        python -m pip install pytest==7.4.2 black==23.7.0 flake8==6.0.0 --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "⚠️  Warning: Error instalando herramientas de desarrollo" $ColorWarning
        }
        
        Write-ColorOutput "✅ Dependencias instaladas correctamente" $ColorSuccess
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error instalando dependencias: $($_.Exception.Message)" $ColorError
        return $false
    }
}

function Test-Installation {
    Write-ColorOutput "🧪 Verificando instalación..." $ColorInfo
    
    try {
        # Probar imports básicos
        $testScript = @"
import sys
import os
sys.path.append('.')

# Test imports
try:
    from configuracion.configuracion_general import obtener_config
    from utilidades.logger import obtener_logger_sistema
    from protocolos.modbus.cliente_modbus import ClienteModbus
    from modelos.dispositivo import Dispositivo
    print("✅ Todos los módulos se importaron correctamente")
except Exception as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)
"@
        
        $testScript | python
        if ($LASTEXITCODE -ne 0) {
            throw "Error en verificación de módulos"
        }
        
        Write-ColorOutput "✅ Instalación verificada correctamente" $ColorSuccess
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error en verificación: $($_.Exception.Message)" $ColorError
        return $false
    }
}

function Initialize-Configuration {
    Write-ColorOutput "⚙️  Inicializando configuración..." $ColorInfo
    
    # Crear directorios necesarios
    $dirs = @("logs", "base_datos", "temp", "backups")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput "📁 Creado directorio: $dir" $ColorInfo
        }
    }
    
    # Verificar archivo de configuración
    if (Test-Path "configuracion.env") {
        Write-ColorOutput "✅ Archivo de configuración encontrado" $ColorSuccess
    } else {
        Write-ColorOutput "⚠️  Archivo configuracion.env no encontrado" $ColorWarning
        Write-ColorOutput "💡 Crear configuracion.env basado en el ejemplo" $ColorWarning
    }
    
    return $true
}

function Invoke-Tests {
    if (-not $RunTests) {
        return $true
    }
    
    Write-ColorOutput "🧪 Ejecutando pruebas del Módulo 1..." $ColorInfo
    
    if (-not (Test-Path "pruebas\test_modulo1.py")) {
        Write-ColorOutput "⚠️  Archivo de pruebas no encontrado" $ColorWarning
        return $true
    }
    
    try {
        python pruebas\test_modulo1.py
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Todas las pruebas pasaron" $ColorSuccess
        } else {
            Write-ColorOutput "⚠️  Algunas pruebas fallaron (revisar output)" $ColorWarning
        }
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error ejecutando pruebas: $($_.Exception.Message)" $ColorError
        return $false
    }
}

function Show-Summary {
    param([bool]$Success)
    
    Write-ColorOutput "`n===========================================================================" $ColorInfo
    if ($Success) {
        Write-ColorOutput "🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE" $ColorSuccess
    } else {
        Write-ColorOutput "❌ INSTALACIÓN INCOMPLETA" $ColorError
    }
    Write-ColorOutput "===========================================================================" $ColorInfo
    
    if ($Success) {
        Write-Host ""
        Write-ColorOutput "✅ El Módulo 1 del Sistema BMS Demo está listo para usar" $ColorSuccess
        Write-Host ""
        Write-ColorOutput "PRÓXIMOS PASOS:" $ColorInfo
        Write-Host "1. Revisar configuracion.env y ajustar IPs según tu red"
        Write-Host "2. Ejecutar: python main.py"
        Write-Host "3. Verificar logs en ./logs/"
        Write-Host ""
        Write-ColorOutput "COMANDOS ÚTILES:" $ColorInfo
        Write-Host "- Activar entorno: .\entorno_bms\Scripts\Activate.ps1"
        Write-Host "- Ejecutar pruebas: python pruebas\test_modulo1.py"
        Write-Host "- Ver ayuda: python main.py --help"
        Write-Host ""
        Write-ColorOutput "📚 Ver README.md para documentación completa" $ColorInfo
    } else {
        Write-Host ""
        Write-ColorOutput "❌ La instalación no se completó correctamente" $ColorError
        Write-Host ""
        Write-ColorOutput "SOLUCIÓN DE PROBLEMAS:" $ColorWarning
        Write-Host "1. Verificar que Python 3.10+ esté instalado"
        Write-Host "2. Verificar conectividad a internet"
        Write-Host "3. Ejecutar PowerShell como administrador"
        Write-Host "4. Revisar los errores mostrados arriba"
    }
    
    Write-ColorOutput "`n===========================================================================" $ColorInfo
}

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    $startTime = Get-Date
    
    Write-ColorOutput "===========================================================================" $ColorInfo
    Write-ColorOutput "🚀 INSTALADOR AUTOMÁTICO - SISTEMA BMS DEMO MÓDULO 1" $ColorInfo
    Write-ColorOutput "===========================================================================" $ColorInfo
    Write-ColorOutput "Inicio: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" $ColorInfo
    Write-Host ""
    
    $steps = @(
        @{ Name = "Verificar Python"; Function = { Test-PythonInstallation } },
        @{ Name = "Verificar Política de Ejecución"; Function = { Test-ExecutionPolicy } },
        @{ Name = "Verificar Estructura"; Function = { Test-ProjectStructure } },
        @{ Name = "Crear Entorno Virtual"; Function = { New-VirtualEnvironment } },
        @{ Name = "Activar Entorno Virtual"; Function = { Enable-VirtualEnvironment } },
        @{ Name = "Instalar Dependencias"; Function = { Install-Dependencies } },
        @{ Name = "Verificar Instalación"; Function = { Test-Installation } },
        @{ Name = "Inicializar Configuración"; Function = { Initialize-Configuration } },
        @{ Name = "Ejecutar Pruebas"; Function = { Invoke-Tests } }
    )
    
    $success = $true
    $stepNumber = 1
    
    foreach ($step in $steps) {
        Write-ColorOutput "[$stepNumber/$($steps.Count)] $($step.Name)..." $ColorInfo
        $stepResult = & $step.Function
        
        if (-not $stepResult) {
            $success = $false
            Write-ColorOutput "❌ Falló el paso: $($step.Name)" $ColorError
            break
        }
        
        $stepNumber++
        Write-Host ""
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-ColorOutput "Duración total: $($duration.TotalSeconds.ToString('F1')) segundos" $ColorInfo
    
    Show-Summary -Success $success
    
    if ($success) {
        exit 0
    } else {
        exit 1
    }
}

# ============================================================================
# EJECUCIÓN
# ============================================================================
try {
    Main
}
catch {
    Write-ColorOutput "❌ Error fatal: $($_.Exception.Message)" $ColorError
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" $ColorError
    exit 1
}