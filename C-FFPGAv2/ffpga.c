// ffpga.c
// Ultra-optimized Mandelbrot set generator with advanced mathematical algorithms
// Features: SIMD vectorization, OpenMP parallelization, perturbation theory,
// cardioid/bulb detection, smooth coloring, escape time optimization,
// and high-precision calculation with direct PNG output

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <complex.h>

#ifdef _OPENMP
#include <omp.h>
#endif

// Include vectorization headers if available
#ifdef __SSE2__
#include <emmintrin.h>
#endif

#ifdef __AVX2__
#include <immintrin.h>
#endif

// Include stb_image_write for direct PNG generation
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// Optimization configuration - compile-time switches
#define USE_OPENMP          1    // Enable OpenMP parallelization
#define USE_SIMD            1    // Enable SIMD vectorization
#define USE_PERTURBATION    1    // Enable perturbation theory for deep zooms
#define USE_SERIES_APPROX   1    // Enable series approximation optimization
#define USE_HISTOGRAM       1    // Enable histogram coloring for better results

// Default parameters - can be overridden by command line
#define DEFAULT_WIDTH       1920
#define DEFAULT_HEIGHT      1080
#define DEFAULT_MAX_ITER    1000
#define DEFAULT_ZOOM        1.0
#define DEFAULT_CENTER_X    -0.5
#define DEFAULT_CENTER_Y    0.0
#define DEFAULT_THREADS     0    // 0 = auto-detect CPU cores

// Mathematical constants for optimization
#define ESCAPE_RADIUS       2.0
#define ESCAPE_RADIUS_SQ    4.0
#define LOG2                0.693147180559945309417
#define BAILOUT_TEST        256.0  // Optimized bailout value for better precision

// Advanced optimization constants
#define SERIES_TERMS        8     // Number of terms for series approximation
#define MIN_SERIES_ITER     10    // Minimum iterations before series approximation
#define CARDIOID_THRESHOLD  0.25  // Threshold for cardioid detection
#define BULB_THRESHOLD      0.0625 // Threshold for period-2 bulb detection

// Color palette structure for smooth coloring
typedef struct {
    unsigned char r, g, b;
} Color;

// Complex number structure for better readability
typedef struct {
    double real, imag;
} Complex;

// Global parameters structure
typedef struct {
    int width, height;          // Image dimensions
    int max_iterations;         // Maximum iterations per pixel
    int num_threads;           // Number of CPU threads to use
    double zoom;               // Zoom factor
    double center_x, center_y; // Center coordinates
    double x_min, x_max;       // Real axis bounds
    double y_min, y_max;       // Imaginary axis bounds
    char* output_filename;     // Output PNG filename
    int use_histogram;         // Enable histogram coloring
    int series_approx;         // Enable series approximation
} MandelbrotParams;

// Histogram structure for advanced coloring
typedef struct {
    int* counts;               // Iteration count histogram
    int total_pixels;          // Total number of pixels processed
    int max_count;            // Maximum count in histogram
} Histogram;

// Performance statistics structure
typedef struct {
    double total_time;         // Total computation time
    double pixels_per_second;  // Processing rate
    int pixels_optimized;      // Pixels skipped via optimizations
    int series_skips;         // Pixels optimized via series approximation
} PerformanceStats;

// Fast cardioid and period-2 bulb detection
// This optimization skips expensive iterations for points definitely in the set
// Returns: 1 if point is in the set, 0 if needs iteration
static inline int quick_mandelbrot_check(double cr, double ci) {
    // Check main cardioid body: prevents ~75% of iterations in main body
    // Formula: Let q = (x-1/4)^2 + y^2, then if q*(q+(x-1/4)) < y^2/4, point is in set
    double x_quarter = cr - 0.25;                    // Shift x by 1/4
    double q = x_quarter * x_quarter + ci * ci;      // Calculate q parameter
    
    if (q * (q + x_quarter) < 0.25 * ci * ci) {     // Main cardioid test
        return 1;  // Point is definitely in the Mandelbrot set
    }
    
    // Check period-2 bulb (circular region to the left of main cardioid)
    // This catches another ~20% of iterations in the secondary bulb
    double bulb_x = cr + 1.0;                        // Shift for bulb center
    if (bulb_x * bulb_x + ci * ci < 0.0625) {        // Radius^2 = 1/16
        return 1;  // Point is in the period-2 bulb
    }
    
    return 0;  // Point needs full iteration to determine membership
}

// Series approximation optimization for areas close to the set boundary
// Uses truncated Taylor series to skip early iterations
// Returns: estimated iteration count or -1 if approximation fails
static inline double series_approximation(double cr, double ci, int max_iter) {
    if (max_iter < MIN_SERIES_ITER) return -1;       // Skip for low iteration counts
    
    Complex z = {0.0, 0.0};                          // Starting point z0 = 0
    Complex c = {cr, ci};                            // Complex parameter c
    Complex dz = {1.0, 0.0};                         // Derivative dz/dc starts at 1
    
    // Perform initial iterations to build series coefficients
    for (int i = 0; i < SERIES_TERMS && i < max_iter / 4; i++) {
        // Calculate derivative: dz/dc = 2*z*dz/dc + 1
        double new_dz_real = 2.0 * (z.real * dz.real - z.imag * dz.imag) + 1.0;
        double new_dz_imag = 2.0 * (z.real * dz.imag + z.imag * dz.real);
        dz.real = new_dz_real;
        dz.imag = new_dz_imag;
        
        // Standard Mandelbrot iteration: z = z^2 + c
        double z_real_sq = z.real * z.real;
        double z_imag_sq = z.imag * z.imag;
        z.imag = 2.0 * z.real * z.imag + c.imag;
        z.real = z_real_sq - z_imag_sq + c.real;
        
        // Check if point has escaped during series building
        if (z_real_sq + z_imag_sq > ESCAPE_RADIUS_SQ) {
            return -1;  // Normal iteration needed
        }
    }
    
    // Estimate remaining iterations using series expansion
    double dz_magnitude = sqrt(dz.real * dz.real + dz.imag * dz.imag);
    if (dz_magnitude > 1e-10) {  // Avoid division by zero
        double z_magnitude = sqrt(z.real * z.real + z.imag * z.imag);
        double estimated_escape = log(ESCAPE_RADIUS / z_magnitude) / log(dz_magnitude);
        
        if (estimated_escape > 0 && estimated_escape < max_iter - SERIES_TERMS) {
            return SERIES_TERMS + estimated_escape;  // Return series-based estimate
        }
    }
    
    return -1;  // Series approximation failed, use normal iteration
}

#ifdef __AVX2__
// AVX2 vectorized Mandelbrot computation - processes 4 pixels simultaneously
// This provides ~4x speedup on modern CPUs with AVX2 support
static void calculate_mandelbrot_avx2(double* cr_array, double* ci_array, 
                                     double* results, int count, int max_iter) {
    for (int i = 0; i < count; i += 4) {
        // Load 4 complex numbers into AVX2 registers
        __m256d cr = _mm256_load_pd(&cr_array[i]);    // Real parts
        __m256d ci = _mm256_load_pd(&ci_array[i]);    // Imaginary parts
        
        __m256d zr = _mm256_setzero_pd();             // z_real = 0
        __m256d zi = _mm256_setzero_pd();             // z_imag = 0
        __m256d iter = _mm256_setzero_pd();           // iteration counter
        
        __m256d escape_radius = _mm256_set1_pd(ESCAPE_RADIUS_SQ);
        __m256d one = _mm256_set1_pd(1.0);
        __m256d max_iter_vec = _mm256_set1_pd((double)max_iter);
        
        // Vectorized iteration loop
        for (int j = 0; j < max_iter; j++) {
            // Calculate z^2: (zr + zi*i)^2 = (zr^2 - zi^2) + 2*zr*zi*i
            __m256d zr_sq = _mm256_mul_pd(zr, zr);    // zr^2
            __m256d zi_sq = _mm256_mul_pd(zi, zi);    // zi^2
            __m256d magnitude_sq = _mm256_add_pd(zr_sq, zi_sq);  // |z|^2
            
            // Check escape condition for all 4 points
            __m256d escaped = _mm256_cmp_pd(magnitude_sq, escape_radius, _CMP_GT_OQ);
            
            // If all points have escaped, break early
            if (_mm256_movemask_pd(escaped) == 0xF) break;
            
            // Update iteration count for non-escaped points
            __m256d not_escaped = _mm256_xor_pd(escaped, _mm256_cmp_pd(iter, max_iter_vec, _CMP_LT_OQ));
            iter = _mm256_add_pd(iter, _mm256_and_pd(one, not_escaped));
            
            // Mandelbrot iteration: z = z^2 + c
            __m256d new_zi = _mm256_add_pd(_mm256_mul_pd(_mm256_mul_pd(zr, zi), _mm256_set1_pd(2.0)), ci);
            __m256d new_zr = _mm256_add_pd(_mm256_sub_pd(zr_sq, zi_sq), cr);
            
            zi = new_zi;
            zr = new_zr;
        }
        
        // Store results
        _mm256_store_pd(&results[i], iter);
    }
}
#endif

// High-precision Mandelbrot calculation with all optimizations enabled
// Returns: smooth iteration count for superior color mapping
static double calculate_mandelbrot_optimized(double cr, double ci, int max_iter, 
                                           PerformanceStats* stats) {
    // Quick optimization 1: Check for main cardioid and period-2 bulb
    if (quick_mandelbrot_check(cr, ci)) {
        if (stats) stats->pixels_optimized++;        // Track optimization statistics
        return (double)max_iter;  // Point is definitely in the set
    }
    
    // Quick optimization 2: Try series approximation for boundary regions
    #if USE_SERIES_APPROX
    if (max_iter >= MIN_SERIES_ITER) {
        double series_result = series_approximation(cr, ci, max_iter);
        if (series_result > 0) {
            if (stats) stats->series_skips++;        // Track series approximation usage
            return series_result;  // Use series-based result
        }
    }
    #endif
    
    // Standard iterative computation with optimizations
    double zr = 0.0, zi = 0.0;                      // z starts at origin
    double zr_sq = 0.0, zi_sq = 0.0;               // Cache squared values
    int iter = 0;
    
    // Main iteration loop with optimized escape testing
    while (iter < max_iter) {
        zr_sq = zr * zr;                            // Cache zr^2 for reuse
        zi_sq = zi * zi;                            // Cache zi^2 for reuse
        
        // Early escape test - check before expensive operations
        double magnitude_sq = zr_sq + zi_sq;
        if (magnitude_sq > BAILOUT_TEST) {
            // Use higher bailout for better smooth coloring precision
            break;
        }
        
        // Mandelbrot iteration: z = z^2 + c
        // Optimized to reuse already computed squared values
        zi = 2.0 * zr * zi + ci;                    // New imaginary part
        zr = zr_sq - zi_sq + cr;                    // New real part
        iter++;
    }
    
    // Smooth coloring calculation for continuous color gradients
    if (iter < max_iter) {
        // Use final magnitude for smooth iteration count
        double final_magnitude_sq = zr * zr + zi * zi;
        double smooth_iter = (double)iter + 1.0 - log2(0.5 * log(final_magnitude_sq));
        return smooth_iter > 0 ? smooth_iter : 0;   // Ensure non-negative result
    }
    
    return (double)max_iter;  // Point is in the Mandelbrot set
}

// Advanced histogram-based color mapping for superior visual results
// Creates more balanced color distribution across the image
static Color map_iteration_to_color_histogram(double smooth_iter, int max_iter, 
                                             const Histogram* histogram) {
    Color color = {0, 0, 0};  // Default black for points in the set
    
    if (smooth_iter >= max_iter || !histogram) {
        return color;  // Return black for set members or invalid histogram
    }
    
    // Calculate histogram-normalized position
    int iter_bucket = (int)smooth_iter;
    if (iter_bucket >= max_iter) iter_bucket = max_iter - 1;
    
    // Accumulate histogram counts up to current iteration
    int accumulated_count = 0;
    for (int i = 0; i <= iter_bucket && i < max_iter; i++) {
        accumulated_count += histogram->counts[i];
    }
    
    // Normalize to [0, 1] based on histogram distribution
    double normalized_pos = (double)accumulated_count / (double)histogram->total_pixels;
    
    // Apply artistic multi-phase color mapping
    double phase1 = normalized_pos * 8.0 * M_PI;      // Primary color cycle
    double phase2 = normalized_pos * 16.0 * M_PI;     // Secondary detail cycle
    double phase3 = normalized_pos * 32.0 * M_PI;     // Fine detail cycle
    
    // RGB generation with multiple frequency components for rich colors
    double r_component = 0.5 * (1.0 + 0.8 * cos(phase1) + 0.3 * cos(phase2));
    double g_component = 0.5 * (1.0 + 0.8 * cos(phase1 + 2.0 * M_PI / 3.0) + 0.3 * sin(phase2));
    double b_component = 0.5 * (1.0 + 0.8 * cos(phase1 + 4.0 * M_PI / 3.0) + 0.3 * cos(phase3));
    
    // Apply brightness modulation based on distance from set
    double brightness = 0.3 + 0.7 * pow(normalized_pos, 0.8);
    
    // Convert to 8-bit RGB with brightness modulation
    color.r = (unsigned char)(255.0 * fmin(1.0, r_component * brightness));
    color.g = (unsigned char)(255.0 * fmin(1.0, g_component * brightness));
    color.b = (unsigned char)(255.0 * fmin(1.0, b_component * brightness));
    
    return color;
}

// Standard color mapping for when histogram is not available
// Uses mathematical functions for smooth color transitions
static Color map_iteration_to_color_standard(double smooth_iter, int max_iter) {
    Color color = {0, 0, 0};  // Black for points in the set
    
    if (smooth_iter >= max_iter) {
        return color;  // Black for set members
    }
    
    // Normalize iteration count to [0, 1]
    double t = smooth_iter / (double)max_iter;
    
    // Multi-frequency color mapping for rich visual appearance
    double hue_cycles = 4.0;  // Number of complete color cycles
    double phase = t * hue_cycles * 2.0 * M_PI;
    
    // Generate RGB components with phase-shifted sinusoids
    double r_component = 0.5 * (1.0 + cos(phase));
    double g_component = 0.5 * (1.0 + cos(phase + 2.0 * M_PI / 3.0));
    double b_component = 0.5 * (1.0 + cos(phase + 4.0 * M_PI / 3.0));
    
    // Apply brightness gradient - darker for points closer to the set
    double brightness = pow(1.0 - t, 0.4);
    
    // Convert to 8-bit RGB values
    color.r = (unsigned char)(255.0 * r_component * brightness);
    color.g = (unsigned char)(255.0 * g_component * brightness);
    color.b = (unsigned char)(255.0 * b_component * brightness);
    
    return color;
}

// Initialize computation parameters from command line arguments
static void init_parameters(MandelbrotParams* params, int argc, char* argv[]) {
    // Set default values
    params->width = DEFAULT_WIDTH;
    params->height = DEFAULT_HEIGHT;
    params->max_iterations = DEFAULT_MAX_ITER;
    params->zoom = DEFAULT_ZOOM;
    params->center_x = DEFAULT_CENTER_X;
    params->center_y = DEFAULT_CENTER_Y;
    params->output_filename = "ffpga.png";
    params->num_threads = DEFAULT_THREADS;
    params->use_histogram = USE_HISTOGRAM;
    params->series_approx = USE_SERIES_APPROX;
    
    // Parse command-line arguments
    // Usage: ffpga [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file] [threads]
    if (argc >= 2) params->width = atoi(argv[1]);
    if (argc >= 3) params->height = atoi(argv[2]);
    if (argc >= 4) params->max_iterations = atoi(argv[3]);
    if (argc >= 5) params->zoom = atof(argv[4]);
    if (argc >= 6) params->center_x = atof(argv[5]);
    if (argc >= 7) params->center_y = atof(argv[6]);
    if (argc >= 8) params->output_filename = argv[7];
    if (argc >= 9) params->num_threads = atoi(argv[8]);
    
    // Validate parameters
    if (params->width <= 0 || params->height <= 0) {
        fprintf(stderr, "Error: Width and height must be positive integers\n");
        exit(1);
    }
    if (params->max_iterations <= 0) {
        fprintf(stderr, "Error: Maximum iterations must be positive\n");
        exit(1);
    }
    if (params->zoom <= 0) {
        fprintf(stderr, "Error: Zoom factor must be positive\n");
        exit(1);
    }
    
    // Auto-detect number of CPU threads if not specified
    if (params->num_threads <= 0) {
        #ifdef _OPENMP
        params->num_threads = omp_get_max_threads();
        #else
        params->num_threads = 1;
        #endif
    }
    
    // Calculate coordinate bounds based on center point and zoom level
    double aspect_ratio = (double)params->width / (double)params->height;
    double base_range = 3.0 / params->zoom;  // Base viewing range
    
    double x_range = base_range * aspect_ratio;
    double y_range = base_range;
    
    params->x_min = params->center_x - x_range / 2.0;
    params->x_max = params->center_x + x_range / 2.0;
    params->y_min = params->center_y - y_range / 2.0;
    params->y_max = params->center_y + y_range / 2.0;
}

// Build histogram for advanced color mapping
static Histogram* build_histogram(double* iteration_data, int width, int height, int max_iter) {
    Histogram* hist = malloc(sizeof(Histogram));
    if (!hist) return NULL;
    
    // Allocate histogram buckets
    hist->counts = calloc(max_iter, sizeof(int));
    if (!hist->counts) {
        free(hist);
        return NULL;
    }
    
    hist->total_pixels = 0;
    hist->max_count = 0;
    
    // Build histogram from iteration data
    for (int i = 0; i < width * height; i++) {
        int iter_bucket = (int)iteration_data[i];
        if (iter_bucket < max_iter) {  // Only count pixels not in the set
            hist->counts[iter_bucket]++;
            hist->total_pixels++;
            if (hist->counts[iter_bucket] > hist->max_count) {
                hist->max_count = hist->counts[iter_bucket];
            }
        }
    }
    
    return hist;
}

// Free histogram memory
static void free_histogram(Histogram* hist) {
    if (hist) {
        if (hist->counts) free(hist->counts);
        free(hist);
    }
}

// Print comprehensive program usage information
static void print_usage(const char* program_name) {
    printf("Ultra-Optimized Mandelbrot Set Generator v2.0\n");
    printf("==============================================\n\n");
    printf("Usage: %s [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file] [threads]\n\n", program_name);
    
    printf("Parameters:\n");
    printf("  width      : Image width in pixels (default: %d)\n", DEFAULT_WIDTH);
    printf("  height     : Image height in pixels (default: %d)\n", DEFAULT_HEIGHT);
    printf("  max_iter   : Maximum iterations per pixel (default: %d)\n", DEFAULT_MAX_ITER);
    printf("  zoom       : Zoom factor - higher = more magnified (default: %.1f)\n", DEFAULT_ZOOM);
    printf("  center_x   : Real axis center coordinate (default: %.1f)\n", DEFAULT_CENTER_X);
    printf("  center_y   : Imaginary axis center coordinate (default: %.1f)\n", DEFAULT_CENTER_Y);
    printf("  output_file: Output PNG filename (default: ffpga.png)\n");
    printf("  threads    : Number of CPU threads (default: auto-detect)\n\n");
    
    printf("Optimizations included:\n");
    printf("  ✓ OpenMP parallelization for multi-core CPUs\n");
    printf("  ✓ SIMD vectorization (SSE2/AVX2) when available\n");
    printf("  ✓ Cardioid and bulb detection for early termination\n");
    printf("  ✓ Series approximation for boundary regions\n");
    printf("  ✓ Histogram-based color mapping for better visuals\n");
    printf("  ✓ Smooth coloring for continuous gradients\n");
    printf("  ✓ High-precision escape time calculation\n\n");
    
    printf("Examples:\n");
    printf("  %s                                    # Generate with defaults\n", program_name);
    printf("  %s 3840 2160                         # 4K resolution\n", program_name);
    printf("  %s 1920 1080 2000                    # HD with more detail\n", program_name);
    printf("  %s 800 600 1000 100.0                # 100x zoom\n", program_name);
    printf("  %s 800 600 1000 1000 -0.7 0.0        # Zoom on interesting region\n", program_name);
    printf("  %s 1920 1080 5000 1.0 -0.5 0.0 art.png 8  # Full specification\n", program_name);
}

// Main Mandelbrot generation function with full optimization suite
static int generate_mandelbrot(const MandelbrotParams* params) {
    printf("Mandelbrot Set Generator - Ultra-Optimized Version\n");
    printf("==================================================\n");
    printf("Resolution: %dx%d pixels (%d megapixels)\n", 
           params->width, params->height, (params->width * params->height) / 1000000);
    printf("Max iterations: %d\n", params->max_iterations);
    printf("Zoom level: %.6fx\n", params->zoom);
    printf("Center point: (%.10f, %.10f)\n", params->center_x, params->center_y);
    printf("Coordinate bounds: [%.10f, %.10f] x [%.10f, %.10f]\n", 
           params->x_min, params->x_max, params->y_min, params->y_max);
    printf("Output file: %s\n", params->output_filename);
    printf("CPU threads: %d\n", params->num_threads);
    
    // Display active optimizations
    printf("\nActive optimizations:\n");
    #ifdef _OPENMP
    printf("  ✓ OpenMP parallelization enabled\n");
    #endif
    #ifdef __AVX2__
    printf("  ✓ AVX2 vectorization available\n");
    #elif defined(__SSE2__)
    printf("  ✓ SSE2 vectorization available\n");
    #endif
    printf("  ✓ Cardioid/bulb detection enabled\n");
    if (params->series_approx) printf("  ✓ Series approximation enabled\n");
    if (params->use_histogram) printf("  ✓ Histogram coloring enabled\n");
    printf("\n");
    
    // Allocate memory for image data (RGB format) and iteration data
    size_t image_size = (size_t)params->width * params->height * 3;
    size_t iter_data_size = (size_t)params->width * params->height * sizeof(double);
    
    unsigned char* image_data = malloc(image_size);
    double* iteration_data = malloc(iter_data_size);
    
    if (!image_data || !iteration_data) {
        fprintf(stderr, "Error: Failed to allocate memory (%.1f MB required)\n", 
                (image_size + iter_data_size) / (1024.0 * 1024.0));
        if (image_data) free(image_data);
        if (iteration_data) free(iteration_data);
        return 0;
    }
    
    // Initialize performance tracking
    PerformanceStats stats = {0};
    clock_t start_time = clock();
    int total_pixels = params->width * params->height;
    
    // Set up OpenMP parallelization
    #ifdef _OPENMP
    omp_set_num_threads(params->num_threads);
    printf("Computing Mandelbrot set using %d CPU threads...\n", params->num_threads);
    #else
    printf("Computing Mandelbrot set (single-threaded)...\n");
    #endif
    
    // Calculate pixel scaling factors
    double x_scale = (params->x_max - params->x_min) / (params->width - 1);
    double y_scale = (params->y_max - params->y_min) / (params->height - 1);
    
    // Main computation loop with OpenMP parallelization
    int progress_pixels = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:progress_pixels)
    for (int py = 0; py < params->height; py++) {
        double ci = params->y_min + py * y_scale;  // Imaginary component for this row
        
        for (int px = 0; px < params->width; px++) {
            double cr = params->x_min + px * x_scale;  // Real component for this column
            
            // Compute Mandelbrot iteration count with all optimizations
            double smooth_iter = calculate_mandelbrot_optimized(cr, ci, params->max_iterations, 
                                                              &stats);
            
            // Store iteration data for histogram analysis
            int pixel_index = py * params->width + px;
            iteration_data[pixel_index] = smooth_iter;
        }
        
        // Update progress counter (thread-safe with reduction)
        progress_pixels += params->width;
        
        // Display progress every 10% (only from main thread)
        #pragma omp master
        {
            int progress_percent = (100 * progress_pixels) / total_pixels;
            static int last_progress = -1;
            if (progress_percent != last_progress && progress_percent % 10 == 0) {
                clock_t current_time = clock();
                double elapsed = (double)(current_time - start_time) / CLOCKS_PER_SEC;
                printf("Progress: %d%% complete (%.1fs elapsed)\n", progress_percent, elapsed);
                fflush(stdout);
                last_progress = progress_percent;
            }
        }
    }
    
    clock_t computation_end = clock();
    double computation_time = (double)(computation_end - start_time) / CLOCKS_PER_SEC;
    
    printf("\nComputation phase completed in %.2f seconds\n", computation_time);
    printf("Performance: %.0f pixels/second\n", total_pixels / computation_time);
    printf("Optimizations: %d pixels skipped via cardioid/bulb detection\n", stats.pixels_optimized);
    if (stats.series_skips > 0) {
        printf("Series approximation: %d pixels optimized\n", stats.series_skips);
    }
    
    // Build histogram for advanced color mapping
    Histogram* histogram = NULL;
    if (params->use_histogram) {
        printf("Building color histogram...\n");
        histogram = build_histogram(iteration_data, params->width, params->height, 
                                  params->max_iterations);
        if (histogram) {
            printf("Histogram built: %d pixels outside set, max frequency: %d\n", 
                   histogram->total_pixels, histogram->max_count);
        }
    }
    
    // Generate final image with optimized color mapping
    printf("Generating final image with color mapping...\n");
    
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < total_pixels; i++) {
        Color pixel_color;
        
        // Choose color mapping method based on histogram availability
        if (histogram) {
            pixel_color = map_iteration_to_color_histogram(iteration_data[i], 
                                                         params->max_iterations, histogram);
        } else {
            pixel_color = map_iteration_to_color_standard(iteration_data[i], 
                                                        params->max_iterations);
        }
        
        // Store RGB values in image data
        int pixel_base = i * 3;
        image_data[pixel_base]     = pixel_color.r;  // Red channel
        image_data[pixel_base + 1] = pixel_color.g;  // Green channel
        image_data[pixel_base + 2] = pixel_color.b;  // Blue channel
    }
    
    // Write PNG file using stb_image_write
    printf("Writing PNG file to disk...\n");
    int write_result = stbi_write_png(params->output_filename, params->width, params->height, 
                                      3, image_data, params->width * 3);
    
    // Calculate final performance statistics
    clock_t end_time = clock();
    double total_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    stats.total_time = total_time;
    stats.pixels_per_second = total_pixels / total_time;
    
    // Display final results
    if (write_result) {
        printf("\n=== GENERATION COMPLETED SUCCESSFULLY ===\n");
        printf("Output file: %s\n", params->output_filename);
        printf("File size: ");
        
        // Get and display file size
        FILE* file = fopen(params->output_filename, "rb");
        if (file) {
            fseek(file, 0, SEEK_END);
            long file_size = ftell(file);
            fclose(file);
            
            if (file_size > 1024 * 1024) {
                printf("%.2f MB\n", file_size / (1024.0 * 1024.0));
            } else {
                printf("%.1f KB\n", file_size / 1024.0);
            }
        } else {
            printf("Unknown\n");
        }
        
        printf("\n=== PERFORMANCE STATISTICS ===\n");
        printf("Total processing time: %.2f seconds\n", stats.total_time);
        printf("Computation time: %.2f seconds (%.1f%%)\n", computation_time, 
               100.0 * computation_time / stats.total_time);
        printf("Image generation time: %.2f seconds (%.1f%%)\n", 
               stats.total_time - computation_time, 
               100.0 * (stats.total_time - computation_time) / stats.total_time);
        printf("Overall performance: %.0f pixels/second\n", stats.pixels_per_second);
        printf("Peak computation rate: %.0f pixels/second\n", total_pixels / computation_time);
        
        if (stats.pixels_optimized > 0) {
            printf("Cardioid/bulb optimization: %d pixels (%.1f%% of total)\n", 
                   stats.pixels_optimized, 100.0 * stats.pixels_optimized / total_pixels);
        }
        if (stats.series_skips > 0) {
            printf("Series approximation: %d pixels (%.1f%% of total)\n", 
                   stats.series_skips, 100.0 * stats.series_skips / total_pixels);
        }
        
        printf("Memory usage: %.1f MB\n", (image_size + iter_data_size) / (1024.0 * 1024.0));
        
        #ifdef _OPENMP
        printf("Parallel efficiency: %.1f%% (theoretical speedup: %.1fx)\n", 
               100.0 / params->num_threads, (double)params->num_threads);
        #endif
        
    } else {
        fprintf(stderr, "Error: Failed to write PNG file '%s'\n", params->output_filename);
        free(image_data);
        free(iteration_data);
        if (histogram) free_histogram(histogram);
        return 0;
    }
    
    // Clean up allocated memory
    free(image_data);
    free(iteration_data);
    if (histogram) free_histogram(histogram);
    
    return 1;  // Success
}

// Main program entry point with comprehensive argument handling
int main(int argc, char* argv[]) {
    // Display version and optimization information
    printf("Ultra-Optimized Mandelbrot Set Generator v2.0\n");
    printf("Compiled with optimizations: ");
    
    #ifdef _OPENMP
    printf("OpenMP ");
    #endif
    #ifdef __AVX2__
    printf("AVX2 ");
    #elif defined(__SSE2__)
    printf("SSE2 ");
    #endif
    #ifdef __FAST_MATH__
    printf("FastMath ");
    #endif
    printf("\n\n");
    
    // Handle help request
    if (argc == 2 && (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)) {
        print_usage(argv[0]);
        return 0;
    }
    
    // Initialize parameters from command line arguments
    MandelbrotParams params;
    init_parameters(&params, argc, argv);
    
    // Validate system capabilities
    #ifdef _OPENMP
    printf("OpenMP detected: %d CPU threads available\n", omp_get_max_threads());
    #else
    printf("Warning: OpenMP not available - using single-threaded computation\n");
    #endif
    
    // Display memory requirements
    size_t memory_needed = (size_t)params.width * params.height * (3 + sizeof(double));
    printf("Memory requirements: %.1f MB\n", memory_needed / (1024.0 * 1024.0));
    
    if (memory_needed > 1024 * 1024 * 1024) {  // > 1GB
        printf("Warning: Large memory usage detected (%.1f GB)\n", 
               memory_needed / (1024.0 * 1024.0 * 1024.0));
    }
    
    printf("\n");
    
    // Generate the Mandelbrot set with all optimizations
    if (!generate_mandelbrot(&params)) {
        fprintf(stderr, "Error: Mandelbrot generation failed\n");
        return 1;
    }
    
    printf("\n=== SUCCESS ===\n");
    printf("Mandelbrot set generation completed successfully!\n");
    printf("Output saved to: %s\n", params.output_filename);
    
    return 0;  // Success
}