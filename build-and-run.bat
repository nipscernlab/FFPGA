@echo off
REM ========================================================================
REM Enhanced ffpga Generator Build and Run Script
REM ========================================================================
REM This script:
REM 1) Downloads required header file (stb_image_write.h) if not present
REM 2) Compiles ffpga.c with maximum optimizations
REM 3) Runs the generator with customizable parameters
REM 4) Displays performance metrics and output information
REM ========================================================================

setlocal EnableDelayedExpansion

REM Configuration - modify these values as needed
set EXECUTABLE_NAME=ffpga.exe
set SOURCE_FILE=ffpga.c
set DEFAULT_WIDTH=1920
set DEFAULT_HEIGHT=1080
set DEFAULT_ITERATIONS=100000000
set DEFAULT_OUTPUT=ffpga.png

echo ========================================================================
echo Ultra-Optimized ffpga Set Generator
echo ========================================================================
echo.

REM ----------------------------------------
REM Step 1: Check and download dependencies
REM ----------------------------------------
echo [1/4] Checking dependencies...

if not exist "stb_image_write.h" (
    echo stb_image_write.h not found. Downloading from GitHub...
    
    REM Try to download using PowerShell (available on Windows 7+)
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h', 'stb_image_write.h')" 2>nul
    
    if not exist "stb_image_write.h" (
        echo.
        echo ERROR: Could not download stb_image_write.h automatically.
        echo Please download it manually from:
        echo https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h
        echo Save it in the same directory as this script.
        echo.
        pause
        exit /b 1
    )
    
    echo Successfully downloaded stb_image_write.h
) else (
    echo stb_image_write.h found.
)

if not exist "%SOURCE_FILE%" (
    echo.
    echo ERROR: Source file %SOURCE_FILE% not found!
    echo Make sure the C source file is in the same directory.
    echo.
    pause
    exit /b 1
)

echo Dependencies check complete.
echo.

REM ----------------------------------------
REM Step 2: Compile with maximum optimizations
REM ----------------------------------------
echo [2/4] Compiling with aggressive optimizations...

REM Record compilation start time
set COMPILE_START_TIME=%TIME%

REM Advanced GCC optimization flags for maximum performance:
REM -O3              : Highest optimization level
REM -march=native    : Optimize for current CPU architecture
REM -mtune=native    : Tune for current CPU
REM -ffast-math      : Enable fast floating-point math (slightly less precise but much faster)
REM -funroll-loops   : Unroll loops for better performance
REM -flto            : Link-time optimization
REM -DNDEBUG         : Disable debug assertions
REM -lm              : Link math library

gcc -O3 -march=native -mtune=native -ffast-math -funroll-loops -flto -DNDEBUG -Wall -Wextra %SOURCE_FILE% -o %EXECUTABLE_NAME% -lm

if ERRORLEVEL 1 (
    echo.
    echo ERROR: Compilation failed!
    echo Make sure you have GCC installed and in your PATH.
    echo.
    echo If you're using MinGW on Windows, try:
    echo gcc -O3 -ffast-math -funroll-loops %SOURCE_FILE% -o %EXECUTABLE_NAME% -lm
    echo.
    pause
    exit /b 1
)

REM Calculate compilation time
set COMPILE_END_TIME=%TIME%
echo Compilation successful! (%EXECUTABLE_NAME% created)
echo.

REM ----------------------------------------
REM Step 3: Run the generator
REM ----------------------------------------
echo [3/4] Running ffpga generator...
echo.

REM Check for command-line arguments to pass to the executable
if "%~1"=="" (
    echo Using default parameters:
    echo - Resolution: %DEFAULT_WIDTH%x%DEFAULT_HEIGHT%
    echo - Max iterations: %DEFAULT_ITERATIONS%
    echo - Output file: %DEFAULT_OUTPUT%
    echo.
    echo To customize, run: %~nx0 [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file]
    echo Example: %~nx0 800 600 2000 10.0 -0.7 0.0 custom.png
    echo.
    
    REM Run with default parameters
    %EXECUTABLE_NAME% %DEFAULT_WIDTH% %DEFAULT_HEIGHT% %DEFAULT_ITERATIONS%
) else (
    echo Using custom parameters: %*
    echo.
    
    REM Run with provided parameters
    %EXECUTABLE_NAME% %*
)

if ERRORLEVEL 1 (
    echo.
    echo ERROR: ffpga generation failed!
    echo Check the error messages above for details.
    echo.
    pause
    exit /b 1
)

echo.

REM ----------------------------------------
REM Step 4: Display results and file information
REM ----------------------------------------
echo [4/4] Generation complete!
echo.

REM Find the generated PNG file
if "%~1"=="" (
    set OUTPUT_FILE=%DEFAULT_OUTPUT%
) else if "%~7"=="" (
    set OUTPUT_FILE=%DEFAULT_OUTPUT%
) else (
    set OUTPUT_FILE=%~7
)

if exist "!OUTPUT_FILE!" (
    echo Output file: !OUTPUT_FILE!
    
    REM Get file size
    for %%A in ("!OUTPUT_FILE!") do (
        set FILE_SIZE=%%~zA
        set /A FILE_SIZE_KB=!FILE_SIZE!/1024
        set /A FILE_SIZE_MB=!FILE_SIZE_KB!/1024
    )
    
    if !FILE_SIZE_MB! GTR 0 (
        echo File size: !FILE_SIZE_MB!.!FILE_SIZE_KB! MB
    ) else (
        echo File size: !FILE_SIZE_KB! KB
    )
    
    echo.
    echo SUCCESS: ffpga set image generated successfully!
    echo.
    echo You can now:
    echo - Open !OUTPUT_FILE! in any image viewer
    echo - Use it in presentations, artwork, or further processing
    echo - Generate more images with different parameters
    
) else (
    echo WARNING: Expected output file !OUTPUT_FILE! not found.
    echo The generation may have completed but saved with a different name.
)

echo.
echo ========================================================================
echo Build and generation process completed!
echo ========================================================================

REM ----------------------------------------
REM Optional: Open the generated image
REM ----------------------------------------
if exist "!OUTPUT_FILE!" (
    echo.
    set /p OPEN_IMAGE="Open the generated image now? (y/N): "
    if /I "!OPEN_IMAGE!"=="y" (
        start "" "!OUTPUT_FILE!"
    )
)

echo.
echo To generate more images with different parameters, run:
echo %~nx0 [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file]
echo.
echo For help with parameters, run: %EXECUTABLE_NAME% --help
echo.

REM Keep window open if run by double-clicking
if "%~1"=="" pause

endlocal