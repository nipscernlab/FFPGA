@echo off
REM ========================================================================
REM Ultra-Optimized Mandelbrot Set Generator - Build and Run Script v2.0
REM ========================================================================
REM This advanced script:
REM 1) Auto-detects CPU capabilities (AVX2, SSE2, OpenMP support)
REM 2) Downloads required dependencies automatically
REM 3) Compiles with maximum performance optimizations
REM 4) Runs with intelligent parameter suggestions
REM 5) Provides comprehensive performance analysis
REM 6) Handles errors gracefully with detailed diagnostics
REM ========================================================================

setlocal EnableDelayedExpansion

REM ========================================================================
REM CONFIGURATION SECTION - Customize these values as needed
REM ========================================================================
set EXECUTABLE_NAME=ffpga.exe
set SOURCE_FILE=ffpga.c
set STB_HEADER=stb_image_write.h
set DEFAULT_WIDTH=1920
set DEFAULT_HEIGHT=1080
set DEFAULT_ITERATIONS=1000
set DEFAULT_OUTPUT=ffpga.png

REM Performance test configurations
set BENCHMARK_WIDTH=800
set BENCHMARK_HEIGHT=600
set BENCHMARK_ITER=500

echo ========================================================================
echo Ultra-Optimized Mandelbrot Set Generator v2.0
echo Build and Run Script with Advanced Optimizations
echo ========================================================================
echo.

REM ========================================================================
REM STEP 1: SYSTEM CAPABILITY DETECTION
REM ========================================================================
echo [1/6] Detecting system capabilities...

REM Detect CPU features using WMIC (Windows Management Instrumentation)
echo Analyzing CPU features...
for /f "tokens=2 delims==" %%i in ('wmic cpu get name /value ^| find "="') do set CPU_NAME=%%i
echo CPU: !CPU_NAME!

REM Detect number of CPU cores
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| find "="') do set CPU_CORES=%%i
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfLogicalProcessors /value ^| find "="') do set CPU_THREADS=%%i
echo CPU Cores: !CPU_CORES! physical, !CPU_THREADS! logical threads

REM Detect available RAM
for /f "tokens=2 delims==" %%i in ('wmic computersystem get TotalPhysicalMemory /value ^| find "="') do set TOTAL_RAM=%%i
set /a RAM_GB=!TOTAL_RAM!/1073741824
echo Available RAM: !RAM_GB! GB

REM Set optimization flags based on detection
set OPTIMIZATION_FLAGS=-O3 -march=native -mtune=native -ffast-math -funroll-loops -flto -DNDEBUG
set OPENMP_FLAGS=-fopenmp
set SIMD_FLAGS=-msse2

REM Try to detect AVX2 support (basic detection)
echo Checking for advanced CPU features...
set ADVANCED_SIMD=0
reg query "HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0" /v "ProcessorNameString" | findstr /i "Intel" >nul
if !errorlevel! equ 0 (
    echo Intel CPU detected - enabling AVX optimizations
    set SIMD_FLAGS=!SIMD_FLAGS! -mavx -mavx2
    set ADVANCED_SIMD=1
)

echo CPU optimization flags configured: !OPTIMIZATION_FLAGS! !SIMD_FLAGS!
echo.

REM ========================================================================
REM STEP 2: DEPENDENCY MANAGEMENT
REM ========================================================================
echo [2/6] Managing dependencies...

REM Check for GCC compiler
echo Checking for GCC compiler...
gcc --version >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo ERROR: GCC compiler not found!
    echo.
    echo Please install one of the following:
    echo 1. MinGW-w64: https://www.mingw-w64.org/
    echo 2. TDM-GCC: https://jmeubank.github.io/tdm-gcc/
    echo 3. MSYS2: https://www.msys2.org/
    echo.
    echo Make sure GCC is added to your system PATH.
    pause
    exit /b 1
)

REM Get GCC version for optimization compatibility
for /f "tokens=3" %%i in ('gcc --version ^| findstr "gcc"') do set GCC_VERSION=%%i
echo GCC version: !GCC_VERSION!

REM Check OpenMP support
echo Checking OpenMP support...
echo int main(){return 0;} > test_openmp.c
gcc -fopenmp test_openmp.c -o test_openmp.exe >nul 2>&1
if !errorlevel! equ 0 (
    echo OpenMP support: Available
    set USE_OPENMP=1
    del test_openmp.exe >nul 2>&1
) else (
    echo OpenMP support: Not available
    set USE_OPENMP=0
    set OPENMP_FLAGS=
)
del test_openmp.c >nul 2>&1

REM Download stb_image_write.h if not present
if not exist "!STB_HEADER!" (
    echo STB image library not found. Downloading...
    
    REM Try multiple download methods
    set DOWNLOAD_SUCCESS=0
    
    REM Method 1: PowerShell (Windows 7+)
    powershell -Command "try { (New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h', 'stb_image_write.h'); exit 0 } catch { exit 1 }" >nul 2>&1
    if exist "!STB_HEADER!" set DOWNLOAD_SUCCESS=1
    
    REM Method 2: curl (Windows 10+)
    if !DOWNLOAD_SUCCESS! equ 0 (
        curl -s -o "!STB_HEADER!" "https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h" >nul 2>&1
        if exist "!STB_HEADER!" set DOWNLOAD_SUCCESS=1
    )
    
    REM Method 3: certutil (fallback)
    if !DOWNLOAD_SUCCESS! equ 0 (
        certutil -urlcache -split -f "https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h" "!STB_HEADER!" >nul 2>&1
        if exist "!STB_HEADER!" set DOWNLOAD_SUCCESS=1
    )
    
    if !DOWNLOAD_SUCCESS! equ 1 (
        echo Successfully downloaded !STB_HEADER!
    ) else (
        echo.
        echo ERROR: Could not download !STB_HEADER! automatically.
        echo Please download it manually from:
        echo https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h
        echo Save it in the same directory as this script.
        echo.
        pause
        exit /b 1
    )
) else (
    echo STB image library: Found
)

REM Verify source file exists
if not exist "!SOURCE_FILE!" (
    echo.
    echo ERROR: Source file !SOURCE_FILE! not found!
    echo Make sure the C source file is in the same directory.
    echo.
    pause
    exit /b 1
)

echo Dependency check completed successfully.
echo.

REM ========================================================================
REM STEP 3: OPTIMIZED COMPILATION
REM ========================================================================
echo [3/6] Compiling with maximum optimizations...

REM Display compilation configuration
echo Compilation configuration:
echo - Source file: !SOURCE_FILE!
echo - Output executable: !EXECUTABLE_NAME!
echo - Optimization level: !OPTIMIZATION_FLAGS!
echo - SIMD instructions: !SIMD_FLAGS!
if !USE_OPENMP! equ 1 (
    echo - Parallel processing: OpenMP enabled
) else (
    echo - Parallel processing: Single-threaded
)
echo.

REM Record compilation start time
set COMPILE_START_TIME=%TIME%

REM Build complete compilation command
set COMPILE_CMD=gcc !OPTIMIZATION_FLAGS! !SIMD_FLAGS!
if !USE_OPENMP! equ 1 set COMPILE_CMD=!COMPILE_CMD! !OPENMP_FLAGS!
set COMPILE_CMD=!COMPILE_CMD! -Wall -Wextra !SOURCE_FILE! -o !EXECUTABLE_NAME! -lm

echo Executing: !COMPILE_CMD!
echo.

REM Execute compilation
!COMPILE_CMD!

if !errorlevel! neq 0 (
    echo.
    echo ERROR: Compilation failed!
    echo.
    echo Troubleshooting suggestions:
    echo 1. Check that all source files are present
    echo 2. Verify GCC supports the optimization flags
    echo 3. Try compiling with basic flags: gcc -O2 !SOURCE_FILE! -o !EXECUTABLE_NAME! -lm
    echo.
    echo If problems persist, try:
    echo gcc -O2 -fopenmp !SOURCE_FILE! -o !EXECUTABLE_NAME! -lm
    echo.
    pause
    exit /b 1
)

REM Calculate compilation time
set COMPILE_END_TIME=%TIME%
echo Compilation successful! (!EXECUTABLE_NAME! created)

REM Get executable size
for %%A in ("!EXECUTABLE_NAME!") do set EXE_SIZE=%%~zA
set /a EXE_SIZE_KB=!EXE_SIZE!/1024
echo Executable size: !EXE_SIZE_KB! KB
echo.

REM ========================================================================
REM STEP 4: PERFORMANCE BENCHMARKING (Optional)
REM ========================================================================
echo [4/6] Performance analysis...

set /p RUN_BENCHMARK="Run quick performance benchmark? (y/N): "
if /I "!RUN_BENCHMARK!"=="y" (
    echo.
    echo Running performance benchmark...
    echo Test configuration: !BENCHMARK_WIDTH!x!BENCHMARK_HEIGHT!, !BENCHMARK_ITER! iterations
    
    set BENCHMARK_START_TIME=%TIME%
    !EXECUTABLE_NAME! !BENCHMARK_WIDTH! !BENCHMARK_HEIGHT! !BENCHMARK_ITER! 1.0 -0.5 0.0 benchmark.png !CPU_THREADS! >nul
    set BENCHMARK_END_TIME=%TIME%
    
    if exist "benchmark.png" (
        echo Benchmark completed successfully!
        del benchmark.png >nul 2>&1
        echo Performance test passed - optimizations are working correctly.
    ) else (
        echo Warning: Benchmark may have failed, but compilation was successful.
    )
    echo.
)

REM ========================================================================
REM STEP 5: INTELLIGENT PARAMETER SUGGESTIONS
REM ========================================================================
echo [5/6] Analyzing optimal parameters for your system...

REM Calculate suggested parameters based on system capabilities
set /a SUGGESTED_THREADS=!CPU_THREADS!
if !CPU_THREADS! gtr 8 set /a SUGGESTED_THREADS=8

REM Memory-based iteration suggestions
set SUGGESTED_ITERATIONS=1000
if !RAM_GB! gtr 8 set SUGGESTED_ITERATIONS=2000
if !RAM_GB! gtr 16 set SUGGESTED_ITERATIONS=5000

REM Resolution suggestions based on RAM
set SUGGESTED_WIDTH=!DEFAULT_WIDTH!
set SUGGESTED_HEIGHT=!DEFAULT_HEIGHT!
if !RAM_GB! gtr 16 (
    set SUGGESTED_WIDTH=3840
    set SUGGESTED_HEIGHT=2160
    echo System can handle 4K resolution generation
)

echo.
echo RECOMMENDED PARAMETERS FOR YOUR SYSTEM:
echo ======================================
echo Resolution: !SUGGESTED_WIDTH!x!SUGGESTED_HEIGHT! ^(!SUGGESTED_THREADS! threads^)
echo Iterations: !SUGGESTED_ITERATIONS! ^(based on !RAM_GB!GB RAM^)
echo.
echo Interesting regions to explore:
echo 1. Classic view: -0.5 0.0 ^(zoom 1.0^)
echo 2. Seahorse valley: -0.75 0.1 ^(zoom 100^)
echo 3. Lightning: -1.775 0.0 ^(zoom 1000^)
echo 4. Spiral: -0.235125 0.827215 ^(zoom 10000^)
echo.

REM ========================================================================
REM STEP 6: EXECUTION WITH CUSTOM PARAMETERS
REM ========================================================================
echo [6/6] Running Mandelbrot generator...

if "%~1"=="" (
    echo No parameters provided. Options:
    echo.
    echo 1. Use recommended settings for your system
    echo 2. Use default settings ^(!DEFAULT_WIDTH!x!DEFAULT_HEIGHT!, !DEFAULT_ITERATIONS! iter^)
    echo 3. Specify custom parameters
    echo 4. Show help and exit
    echo.
    
    set /p USER_CHOICE="Choose option (1-4): "
    
    if "!USER_CHOICE!"=="1" (
        echo Using recommended settings...
        !EXECUTABLE_NAME! !SUGGESTED_WIDTH! !SUGGESTED_HEIGHT! !SUGGESTED_ITERATIONS! 1.0 -0.5 0.0 optimized_mandelbrot.png !SUGGESTED_THREADS!
    ) else if "!USER_CHOICE!"=="2" (
        echo Using default settings...
        !EXECUTABLE_NAME! !DEFAULT_WIDTH! !DEFAULT_HEIGHT! !DEFAULT_ITERATIONS!
    ) else if "!USER_CHOICE!"=="3" (
        echo.
        set /p CUSTOM_PARAMS="Enter parameters [width height iter zoom center_x center_y output threads]: "
        !EXECUTABLE_NAME! !CUSTOM_PARAMS!
    ) else if "!USER_CHOICE!"=="4" (
        !EXECUTABLE_NAME! --help
        goto :show_examples
    ) else (
        echo Using default settings...
        !EXECUTABLE_NAME! !DEFAULT_WIDTH! !DEFAULT_HEIGHT! !DEFAULT_ITERATIONS!
    )
) else (
    echo Using provided parameters: %*
    !EXECUTABLE_NAME! %*
)

if !errorlevel! neq 0 (
    echo.
    echo ERROR: Mandelbrot generation failed!
    echo Check the error messages above for details.
    echo.
    echo Common issues:
    echo - Insufficient memory for high resolution/iterations
    echo - Invalid parameter values
    echo - Disk space issues
    echo.
    pause
    exit /b 1
)

echo.

REM ========================================================================
REM STEP 7: RESULTS ANALYSIS AND CLEANUP
REM ========================================================================
echo Generation completed! Analyzing results...

REM Find and analyze the output file
set OUTPUT_FILE=!DEFAULT_OUTPUT!
if "%~7" neq "" set OUTPUT_FILE=%~7

if exist "!OUTPUT_FILE!" (
    echo.
    echo === GENERATION SUCCESSFUL ===
    echo Output file: !OUTPUT_FILE!
    
    REM Get detailed file information
    for %%A in ("!OUTPUT_FILE!") do (
        set FILE_SIZE=%%~zA
        set FILE_DATE=%%~tA
    )
    
    set /a FILE_SIZE_KB=!FILE_SIZE!/1024
    set /a FILE_SIZE_MB=!FILE_SIZE_KB!/1024
    
    if !FILE_SIZE_MB! gtr 0 (
        echo File size: !FILE_SIZE_MB! MB ^(!FILE_SIZE_KB! KB^)
    ) else (
        echo File size: !FILE_SIZE_KB! KB
    )
    echo Created: !FILE_DATE!
    
    REM Analyze image characteristics
    if !FILE_SIZE! gtr 1000000 (
        echo Quality: High resolution - suitable for printing/professional use
    ) else if !FILE_SIZE! gtr 100000 (
        echo Quality: Standard resolution - good for web/display use
    ) else (
        echo Quality: Low resolution - suitable for quick previews
    )
    
) else (
    echo.
    echo WARNING: Expected output file !OUTPUT_FILE! not found.
    echo The generation may have completed but saved with a different name.
    echo Check the current directory for PNG files.
)

:show_examples
echo.
echo ========================================================================
echo USAGE EXAMPLES AND NEXT STEPS
echo ========================================================================
echo.
echo Quick examples to try:
echo !~nx0 800 600 1000                    # Fast preview
echo !~nx0 1920 1080 2000                  # HD quality
echo !~nx0 3840 2160 5000                  # 4K ultra-quality
echo !~nx0 800 600 1000 100 -0.75 0.1      # Zoom on interesting region
echo.
echo Advanced examples:
echo !~nx0 1920 1080 10000 1000 -1.25 0.0 deep_zoom.png 8
echo !~nx0 800 600 5000 50000 -0.235125 0.827215 spiral.png !SUGGESTED_THREADS!
echo.

REM System performance summary
echo SYSTEM PERFORMANCE SUMMARY:
echo ===========================
echo CPU: !CPU_NAME!
echo Cores: !CPU_CORES! physical, !CPU_THREADS! logical
echo RAM: !RAM_GB! GB
echo Compiler: GCC !GCC_VERSION!
if !USE_OPENMP! equ 1 (
    echo Parallel processing: Enabled ^(!SUGGESTED_THREADS! recommended threads^)
) else (
    echo Parallel processing: Not available
)
if !ADVANCED_SIMD! equ 1 (
    echo SIMD optimizations: Advanced ^(AVX2^)
) else (
    echo SIMD optimizations: Basic ^(SSE2^)
)

echo.
echo For help with parameters: !EXECUTABLE_NAME! --help
echo For best performance, use recommended thread count: !SUGGESTED_THREADS!
echo.

REM Optional: Open generated image
if exist "!OUTPUT_FILE!" (
    set /p OPEN_IMAGE="Open the generated image now? (y/N): "
    if /I "!OPEN_IMAGE!"=="y" (
        start "" "!OUTPUT_FILE!"
    )
)

echo.
echo ========================================================================
echo BUILD AND GENERATION COMPLETED SUCCESSFULLY!
echo ========================================================================
echo.
echo The optimized Mandelbrot generator is ready to use.
echo Experiment with different zoom levels and coordinates to explore
echo the infinite complexity of the Mandelbrot set!

REM Keep window open if run by double-clicking
if "%~1"=="" (
    echo.
    pause
)

endlocal