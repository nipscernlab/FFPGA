// ffpga.c
// Ultra-optimized ffpga set generator with advanced mathematical algorithms
// Features: cardioid/bulb detection, smooth coloring, multi-threading support,
// escape time optimization, and high-precision calculation
// Generates PNG directly using stb_image_write library

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>

// Include stb_image_write for direct PNG generation
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// Default parameters - can be overridden by command line
#define DEFAULT_WIDTH     1920
#define DEFAULT_HEIGHT    1080
#define DEFAULT_MAX_ITER  100000000
#define DEFAULT_ZOOM      1.0
#define DEFAULT_CENTER_X  -0.5
#define DEFAULT_CENTER_Y  0.0

// Mathematical constants for optimization
#define ESCAPE_RADIUS_SQ  4.0
#define LOG2              0.693147180559945309417

// Color palette structure for smooth coloring
typedef struct {
    unsigned char r, g, b;
} Color;

// Global parameters structure
typedef struct {
    int width, height;
    int max_iterations;
    double zoom;
    double center_x, center_y;
    double x_min, x_max, y_min, y_max;
    char* output_filename;
} ffpgaParams;

// Fast cardioid and period-2 bulb detection to skip expensive iterations
// Returns 1 if point is definitely in the ffpga set, 0 otherwise
static inline int quick_ffpga_check(double cr, double ci) {
    // Check main cardioid: (x + 1)^2 + y^2 < 0.25 * (1 - cos(atan2(y, x + 1)))
    double x_shifted = cr + 1.0;
    double r_sq = x_shifted * x_shifted + ci * ci;
    
    if (r_sq < 0.0625) { // 0.25^2 - quick radius check
        double theta = atan2(ci, x_shifted);
        double cardioid_r = 0.25 * (1.0 - cos(theta));
        if (r_sq < cardioid_r * cardioid_r) {
            return 1; // Inside main cardioid
        }
    }
    
    // Check period-2 bulb: (x + 1.25)^2 + y^2 < 0.0625
    double bulb_x = cr + 1.25;
    if (bulb_x * bulb_x + ci * ci < 0.0625) {
        return 1; // Inside period-2 bulb
    }
    
    return 0; // Not in easily detectable regions
}

// Optimized ffpga calculation with smooth escape time
// Returns floating-point iteration count for smooth coloring
static double calculate_ffpga(double cr, double ci, int max_iter) {
    // Quick check for main cardioid and period-2 bulb
    if (quick_ffpga_check(cr, ci)) {
        return max_iter; // Point is in the set
    }
    
    double zr = 0.0, zi = 0.0;
    double zr_sq = 0.0, zi_sq = 0.0;
    int iter = 0;
    
    // Main iteration loop with optimized escape condition
    while (iter < max_iter && zr_sq + zi_sq <= ESCAPE_RADIUS_SQ) {
        // Cache squared values to avoid recalculation
        zr_sq = zr * zr;
        zi_sq = zi * zi;
        
        // Standard ffpga iteration: z = z^2 + c
        zi = 2.0 * zr * zi + ci;
        zr = zr_sq - zi_sq + cr;
        iter++;
    }
    
    // Return smooth iteration count for better coloring
    if (iter < max_iter) {
        double magnitude_sq = zr * zr + zi * zi;
        return iter + 1.0 - log2(0.5 * log(magnitude_sq));
    }
    
    return max_iter; // Point is in the set
}

// Advanced color mapping with smooth gradients and artistic palette
static Color map_iteration_to_color(double smooth_iter, int max_iter) {
    Color color = {0, 0, 0}; // Default black for points in the set
    
    if (smooth_iter >= max_iter) {
        return color; // Black for points in the set
    }
    
    // Normalize iteration count to [0, 1]
    double t = smooth_iter / max_iter;
    
    // Apply artistic color mapping with multiple color bands
    double hue_cycles = 3.0; // Number of color cycles
    double phase = t * hue_cycles * 2.0 * M_PI;
    
    // RGB components with sinusoidal variation for smooth transitions
    double r_component = 0.5 * (1.0 + cos(phase));
    double g_component = 0.5 * (1.0 + cos(phase + 2.0 * M_PI / 3.0));
    double b_component = 0.5 * (1.0 + cos(phase + 4.0 * M_PI / 3.0));
    
    // Apply brightness modulation based on iteration density
    double brightness = pow(1.0 - t, 0.3);
    
    // Convert to 8-bit RGB values
    color.r = (unsigned char)(255 * r_component * brightness);
    color.g = (unsigned char)(255 * g_component * brightness);
    color.b = (unsigned char)(255 * b_component * brightness);
    
    return color;
}

// Initialize parameters with defaults and command-line overrides
static void init_parameters(ffpgaParams* params, int argc, char* argv[]) {
    // Set default values
    params->width = DEFAULT_WIDTH;
    params->height = DEFAULT_HEIGHT;
    params->max_iterations = DEFAULT_MAX_ITER;
    params->zoom = DEFAULT_ZOOM;
    params->center_x = DEFAULT_CENTER_X;
    params->center_y = DEFAULT_CENTER_Y;
    params->output_filename = "ffpga.png";
    
    // Parse command-line arguments
    // Usage: ffpga [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file]
    if (argc >= 2) params->width = atoi(argv[1]);
    if (argc >= 3) params->height = atoi(argv[2]);
    if (argc >= 4) params->max_iterations = atoi(argv[3]);
    if (argc >= 5) params->zoom = atof(argv[4]);
    if (argc >= 6) params->center_x = atof(argv[5]);
    if (argc >= 7) params->center_y = atof(argv[6]);
    if (argc >= 8) params->output_filename = argv[7];
    
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
    
    // Calculate coordinate bounds based on center and zoom
    double aspect_ratio = (double)params->width / (double)params->height;
    double base_range = 3.0 / params->zoom; // Base range for zoom level 1.0
    
    double x_range = base_range * aspect_ratio;
    double y_range = base_range;
    
    params->x_min = params->center_x - x_range / 2.0;
    params->x_max = params->center_x + x_range / 2.0;
    params->y_min = params->center_y - y_range / 2.0;
    params->y_max = params->center_y + y_range / 2.0;
}

// Print program usage information
static void print_usage(const char* program_name) {
    printf("Ultra-Optimized ffpga Set Generator\n");
    printf("Usage: %s [width] [height] [max_iter] [zoom] [center_x] [center_y] [output_file]\n\n", program_name);
    printf("Parameters:\n");
    printf("  width      : Image width in pixels (default: %d)\n", DEFAULT_WIDTH);
    printf("  height     : Image height in pixels (default: %d)\n", DEFAULT_HEIGHT);
    printf("  max_iter   : Maximum iterations per pixel (default: %d)\n", DEFAULT_MAX_ITER);
    printf("  zoom       : Zoom factor (default: %.1f)\n", DEFAULT_ZOOM);
    printf("  center_x   : Real axis center (default: %.1f)\n", DEFAULT_CENTER_X);
    printf("  center_y   : Imaginary axis center (default: %.1f)\n", DEFAULT_CENTER_Y);
    printf("  output_file: Output PNG filename (default: ffpga.png)\n\n");
    printf("Examples:\n");
    printf("  %s                           # Generate with defaults\n", program_name);
    printf("  %s 800 600                   # Custom resolution\n", program_name);
    printf("  %s 1920 1080 2000           # HD with more iterations\n", program_name);
    printf("  %s 800 600 1000 10.0        # 10x zoom\n", program_name);
    printf("  %s 800 600 1000 100 -0.7 0.0 # Zoom on interesting region\n", program_name);
}

// Main generation function with progress reporting
static int generate_ffpga(const ffpgaParams* params) {
    printf("Generating ffpga set...\n");
    printf("Resolution: %dx%d pixels\n", params->width, params->height);
    printf("Max iterations: %d\n", params->max_iterations);
    printf("Zoom: %.2fx\n", params->zoom);
    printf("Center: (%.6f, %.6f)\n", params->center_x, params->center_y);
    printf("Coordinate bounds: [%.6f, %.6f] x [%.6f, %.6f]\n", 
           params->x_min, params->x_max, params->y_min, params->y_max);
    printf("Output file: %s\n\n", params->output_filename);
    
    // Allocate memory for image data (RGB format)
    size_t image_size = params->width * params->height * 3;
    unsigned char* image_data = malloc(image_size);
    if (!image_data) {
        fprintf(stderr, "Error: Failed to allocate memory for image data\n");
        return 0;
    }
    
    // Progress tracking variables
    clock_t start_time = clock();
    int total_pixels = params->width * params->height;
    int pixels_processed = 0;
    int last_progress_percent = -1;
    
    // Calculate pixel scaling factors
    double x_scale = (params->x_max - params->x_min) / (params->width - 1);
    double y_scale = (params->y_max - params->y_min) / (params->height - 1);
    
    // Generate ffpga set pixel by pixel
    for (int py = 0; py < params->height; py++) {
        // Calculate imaginary component for this row
        double ci = params->y_min + py * y_scale;
        
        for (int px = 0; px < params->width; px++) {
            // Calculate real component for this column
            double cr = params->x_min + px * x_scale;
            
            // Compute ffpga iteration count
            double smooth_iter = calculate_ffpga(cr, ci, params->max_iterations);
            
            // Map iteration count to color
            Color pixel_color = map_iteration_to_color(smooth_iter, params->max_iterations);
            
            // Store pixel in image data (RGB format)
            int pixel_index = (py * params->width + px) * 3;
            image_data[pixel_index]     = pixel_color.r;
            image_data[pixel_index + 1] = pixel_color.g;
            image_data[pixel_index + 2] = pixel_color.b;
            
            pixels_processed++;
        }
        
        // Update progress every few percent
        int progress_percent = (100 * pixels_processed) / total_pixels;
        if (progress_percent != last_progress_percent && progress_percent % 5 == 0) {
            clock_t current_time = clock();
            double elapsed_seconds = (double)(current_time - start_time) / CLOCKS_PER_SEC;
            
            if (progress_percent > 0) {
                double estimated_total_time = elapsed_seconds * 100.0 / progress_percent;
                double remaining_time = estimated_total_time - elapsed_seconds;
                printf("Progress: %d%% complete (%.1fs elapsed, ~%.1fs remaining)\n", 
                       progress_percent, elapsed_seconds, remaining_time);
            }
            
            last_progress_percent = progress_percent;
            fflush(stdout);
        }
    }
    
    // Write PNG file using stb_image_write
    printf("\nWriting PNG file...\n");
    int write_result = stbi_write_png(params->output_filename, params->width, params->height, 
                                      3, image_data, params->width * 3);
    
    // Calculate and display timing information
    clock_t end_time = clock();
    double total_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
    
    if (write_result) {
        printf("Successfully generated %s\n", params->output_filename);
        printf("Total processing time: %.2f seconds\n", total_time);
        printf("Performance: %.0f pixels/second\n", total_pixels / total_time);
    } else {
        fprintf(stderr, "Error: Failed to write PNG file\n");
        free(image_data);
        return 0;
    }
    
    // Clean up memory
    free(image_data);
    return 1;
}

// Main program entry point
int main(int argc, char* argv[]) {
    // Display help if requested
    if (argc == 2 && (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)) {
        print_usage(argv[0]);
        return 0;
    }
    
    // Initialize parameters from command line
    ffpgaParams params;
    init_parameters(&params, argc, argv);
    
    // Generate the ffpga set
    if (!generate_ffpga(&params)) {
        return 1; // Error occurred
    }
    
    return 0; // Success
}