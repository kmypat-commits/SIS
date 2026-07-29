@echo off
chcp 65001 >nul
echo =======================================================
echo          Запуск системы MachOpt-6L (Локально)
echo =======================================================
echo.

:: Переходим в папку со скриптом
cd /d "%~dp0"

:: 1. Проверяем наличие виртуального окружения
if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] Виртуальное окружение Python не найдено в backend\venv!
    echo Выполните установку зависимостей: python -m venv venv ^&^& pip install -r requirements.txt
    pause
    exit /b
)

:: 2. Запуск Backend (FastAPI) в отдельном окне
echo Запускаем Backend (порт 8000)...
start "MachOpt-6L Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

:: Ждём 2 секунды, чтобы бекенд успел стартовать
timeout /t 2 /nobreak >nul

:: 3. Запуск Frontend (Vite) в отдельном окне
echo Запускаем Frontend (порт 5174)...
start "MachOpt-6L Frontend" cmd /k "cd frontend && npm run dev"

:: Ждём 3 секунды
timeout /t 3 /nobreak >nul

:: 4. Открытие браузера
echo Открываем браузер...
start http://localhost:5174/

echo.
echo =======================================================
echo Система успешно запущена!
echo Backend API : http://localhost:8000/docs
echo Frontend UI : http://localhost:5174/
echo.
echo Для остановки серверов закройте два открывшихся черных окна консоли.
echo =======================================================
pause
