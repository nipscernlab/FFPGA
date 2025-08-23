#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Função para mapear iterações para cores (paleta de cores do Mandelbrot)
void get_mandelbrot_color(int iter, int max_iter, unsigned char* r, unsigned char* g, unsigned char* b) {
    if (iter >= max_iter) {
        // Ponto pertencente ao conjunto (preto)
        *r = 0; *g = 0; *b = 0;
    } else {
        // Mapeia iterações para cores usando gradiente
        float t = (float)iter / max_iter;
        
        // Gradiente azul -> ciano -> amarelo -> vermelho -> branco
        if (t < 0.2) {
            float s = t / 0.2;
            *r = 0;
            *g = (unsigned char)(s * 100);
            *b = (unsigned char)(100 + s * 155);
        } else if (t < 0.4) {
            float s = (t - 0.2) / 0.2;
            *r = 0;
            *g = (unsigned char)(100 + s * 155);
            *b = (unsigned char)(255 - s * 100);
        } else if (t < 0.6) {
            float s = (t - 0.4) / 0.2;
            *r = (unsigned char)(s * 255);
            *g = 255;
            *b = (unsigned char)(155 - s * 155);
        } else if (t < 0.8) {
            float s = (t - 0.6) / 0.2;
            *r = 255;
            *g = (unsigned char)(255 - s * 100);
            *b = 0;
        } else {
            float s = (t - 0.8) / 0.2;
            *r = (unsigned char)(255 - s * 50);
            *g = (unsigned char)(155 - s * 155);
            *b = (unsigned char)(s * 200);
        }
    }
}

// Função para salvar imagem no formato PPM
void save_ppm_image(const char* filename, int width, int height, unsigned char* image_data) {
    FILE* fp = fopen(filename, "wb");
    if (!fp) {
        printf("ERRO: Não foi possível criar o arquivo %s\n", filename);
        return;
    }
    
    // Cabeçalho PPM P6 (RGB binário)
    fprintf(fp, "P6\n%d %d\n255\n", width, height);
    
    // Escreve os dados da imagem
    fwrite(image_data, 3, width * height, fp);
    fclose(fp);
    
    printf("✓ Imagem salva como: %s\n", filename);
    printf("  Para visualizar, abra com qualquer visualizador de imagem\n");
    printf("  Ou converta para PNG: magick %s mandelbrot.png\n", filename);
}

// Função para desenhar texto simples (números do timer)
void draw_simple_text(unsigned char* image, int img_width, int img_height, 
                      const char* text, int start_x, int start_y) {
    // Fonte bitmap simples 3x5 para números
    int font_patterns[11][5] = {
        {7, 5, 5, 5, 7}, // 0
        {2, 6, 2, 2, 7}, // 1
        {7, 1, 7, 4, 7}, // 2
        {7, 1, 7, 1, 7}, // 3
        {5, 5, 7, 1, 1}, // 4
        {7, 4, 7, 1, 7}, // 5
        {7, 4, 7, 5, 7}, // 6
        {7, 1, 1, 1, 1}, // 7
        {7, 5, 7, 5, 7}, // 8
        {7, 5, 7, 1, 7}, // 9
        {0, 2, 0, 0, 0}  // . (ponto)
    };
    
    int x = start_x;
    
    for (int i = 0; text[i] != '\0' && x < img_width - 20; i++) {
        int digit = -1;
        
        if (text[i] >= '0' && text[i] <= '9') {
            digit = text[i] - '0';
        } else if (text[i] == '.') {
            digit = 10;
        } else {
            x += 5; // espaço para outros caracteres
            continue;
        }
        
        // Desenha o dígito
        for (int row = 0; row < 5; row++) {
            for (int col = 0; col < 3; col++) {
                if (font_patterns[digit][row] & (1 << (2-col))) {
                    int px = x + col;
                    int py = start_y + row;
                    if (px >= 0 && py >= 0 && px < img_width && py < img_height) {
                        int idx = (py * img_width + px) * 3;
                        image[idx] = 255;     // R - branco
                        image[idx+1] = 255;   // G
                        image[idx+2] = 0;     // B - amarelo
                    }
                }
            }
        }
        x += 5; // espaçamento entre caracteres
    }
}

int main() // ponto de entrada
{
    printf("=== GERADOR DE MANDELBROT FRACTAL ===\n");
    printf("Iniciando cálculos...\n\n");
    
    // Marca o tempo de início da geração do fractal
    clock_t start_time = clock();
    
    // Parâmetros iniciais vindos do XML
    float width = 800.0;    // largura da imagem (px)
    float height = 600.0;   // altura da imagem (px)
    int max_iter = 100;    // iterações máximas por pixel
    
    // Limites da janela do fractal e, portanto, da região de iteração
    float x_min = -3.047291359679012049389;  // limite esquerdo (eixo real)
    float x_max = 1.560661232913579950611;   // limite direito (eixo real)
    float y_min = -1.596716253530864018556;  // limite inferior (eixo imag.)
    float y_max = 1.859248190913580067844;   // limite superior (eixo imag.)
    
    // Escalas para transformar pixels em coordenadas complexas
    float x_scale = (x_max - x_min) / (width - 1);  // passo em x por pixel
    float y_scale = (y_max - y_min) / (height - 1); // passo em y por pixel
    
    // Aloca memória para a imagem (RGB - 3 bytes por pixel)
    int img_width = (int)width;
    int img_height = (int)height;
    unsigned char* image_data = (unsigned char*)malloc(img_width * img_height * 3);
    
    if (!image_data) {
        printf("ERRO: Não foi possível alocar memória para a imagem!\n");
        printf("Pressione Enter para sair...");
        getchar();
        return 1;
    }
    
    int px = 0;  // coluna atual (x)
    int py = 0;  // linha atual (y)
    
    printf("Processando %dx%d pixels (%d total)...\n", img_width, img_height, img_width * img_height);
    printf("Progresso: ");
    fflush(stdout);
    
    // Loop principal de varredura dos pixels
    while(py < height) {  // percorre linhas
        float ci = y_min + py * y_scale;  // parte imaginária do ponto (y)
        px = 0;  // reinicia coluna
        
        // Mostra progresso a cada 10%
        if (py % (img_height / 10) == 0) {
            printf("%.0f%% ", (py / height) * 100);
            fflush(stdout);
        }
        
        while(px < width) {  // percorre colunas
            float cr = x_min + px * x_scale;  // parte real do ponto (x)
            
            // Ponto no plano complexo c = cr + ci*i
            float c_real = cr;
            float c_imag = ci;
            
            // Estado inicial z0 = 0.0 + 0.0i
            float z_real = 0.0;
            float z_imag = 0.0;
            
            float zr_sq = 0.0;  // |Re(z)|^2 (cache)
            float zi_sq = 0.0;  // |Im(z)|^2 (cache)
            int iter = 0;       // contador de iterações
            
            while(iter < max_iter && zr_sq + zi_sq <= 4.0) {  // teste de fuga (|z|^2<=4)
                zr_sq = z_real * z_real;  // atualiza Re(z)^2
                zi_sq = z_imag * z_imag;  // atualiza Im(z)^2
                
                // Iteração: z_{n+1} = z_n^2 + c
                // (a + bi)^2 = a^2 - b^2 + 2abi
                // z^2 + c = (z_real^2 - z_imag^2 + c_real) + (2*z_real*z_imag + c_imag)i
                float temp_real = zr_sq - zi_sq + c_real;
                float temp_imag = 2.0 * z_real * z_imag + c_imag;
                
                z_real = temp_real;
                z_imag = temp_imag;
                
                iter++;  // próximo passo
            }
            
            // Calcula o índice do pixel na imagem
            int pixel_index = (py * img_width + px) * 3;
            
            // Obtém a cor baseada nas iterações e define o pixel
            unsigned char r, g, b;
            get_mandelbrot_color(iter, max_iter, &r, &g, &b);
            
            image_data[pixel_index] = r;     // Red
            image_data[pixel_index + 1] = g; // Green  
            image_data[pixel_index + 2] = b; // Blue
            
            px++;  // próxima coluna
        }
        py++;  // próxima linha
    }
    
    printf("100%%\n");
    
    // Marca o tempo de fim da geração do fractal
    clock_t end_time = clock();
    
    // Calcula o tempo decorrido em segundos
    double time_taken = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
    
    // Adiciona o texto do tempo na imagem
    char time_text[50];
    sprintf(time_text, "%.3fs", time_taken);
    draw_simple_text(image_data, img_width, img_height, time_text, 10, 10);
    
    // Salva a imagem
    save_ppm_image("mandelbrot_fractal.ppm", img_width, img_height, image_data);
    
    // Mostra resultados no console
    printf("\n=== MANDELBROT FRACTAL GERADO ===\n");
    printf("✓ Dimensões: %.0fx%.0f pixels\n", width, height);
    printf("✓ Iterações máximas: %d\n", max_iter);
    printf("✓ Tempo de geração: %.6f segundos\n", time_taken);
    printf("✓ Total de pixels processados: %.0f\n", width * height);
    printf("✓ Velocidade: %.0f pixels/segundo\n", (width * height) / time_taken);
    
    // Libera a memória
    free(image_data);
    
    printf("\n=== PROCESSO CONCLUÍDO ===\n");
    printf("A imagem foi salva no mesmo diretório do executável.\n");
    printf("Abra o arquivo 'mandelbrot_fractal.ppm' com qualquer visualizador de imagem.\n");
    printf("\nPressione Enter para sair...");
    getchar(); // PAUSA o terminal para você ver o resultado
    
    return 0;
}