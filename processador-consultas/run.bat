@echo off
chcp 65001 >nul
cls

echo ======================================
echo Processador de Consultas SQL - HU1/HU2
echo ======================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não está instalado!
    echo Por favor, instale Python 3.8 ou superior
    pause
    exit /b 1
)

echo ✓ Python encontrado
python --version
echo.

REM Criar ambiente virtual se não existir
if not exist "venv\" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
    echo ✓ Ambiente virtual criado
    echo.
)

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependências
echo 📥 Instalando dependências...
pip install -q -r requirements.txt
echo ✓ Dependências instaladas
echo.

REM Perguntar sobre testes
set /p run_tests="Deseja executar os testes? (s/N): "
if /i "%run_tests%"=="s" (
    echo.
    echo 🧪 Executando testes...
    python run_tests.py
    echo.
)

REM Iniciar aplicação
echo 🚀 Iniciando aplicação Flask...
echo 📍 Acesse: http://localhost:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python app.py

pause