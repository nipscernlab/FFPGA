/**
 * Classe para cálculos relacionados ao conjunto de Mandelbrot
 */
class MandelbrotSet {
    constructor() {
      // Valores padrão
      this.maxIterations = 100;
      this.escapeRadius = 2;
      this.escapeRadiusSq = this.escapeRadius * this.escapeRadius;
    }
    
    /**
     * Calcula se um ponto pertence ao conjunto de Mandelbrot
     * @param {number} x - Coordenada real
     * @param {number} y - Coordenada imaginária
     * @returns {number} Número de iterações até escapar (ou maxIterations)
     */
    computePoint(x, y) {
      // Implementação do algoritmo do conjunto de Mandelbrot
      // z = z² + c, onde c é o ponto complexo (x + yi)
      let real = 0;
      let imag = 0;
      let iteration = 0;
      
      // Otimização para cardióide e bulbo de período 2
      const q = (x - 0.25) * (x - 0.25) + y * y;
      if (q * (q + (x - 0.25)) < 0.25 * y * y || 
          (x + 1) * (x + 1) + y * y < 0.0625) {
        return this.maxIterations;
      }
      
      while (iteration < this.maxIterations) {
        // z² = (a + bi)² = a² - b² + 2abi
        const realSquared = real * real;
        const imagSquared = imag * imag;
        
        // Verificar se o ponto escapou
        if (realSquared + imagSquared > this.escapeRadiusSq) {
          break;
        }
        
        // z = z² + c
        const realTemp = realSquared - imagSquared + x;
        imag = 2 * real * imag + y;
        real = realTemp;
        
        iteration++;
      }
      
      // Suavização do valor de escape para cores mais suaves
      if (iteration < this.maxIterations) {
        // Melhorar a visualização com a suavização logarítmica
        const zn = Math.sqrt(real * real + imag * imag);
        const nu = Math.log(Math.log(zn) / Math.log(2)) / Math.log(2);
        iteration = iteration + 1 - nu;
      }
      
      return iteration;
    }
    
    /**
     * Define o número máximo de iterações
     * @param {number} iterations - Número máximo de iterações
     */
    setMaxIterations(iterations) {
      this.maxIterations = iterations;
    }
  }
  
  // Criar objeto global para acessar em outros scripts
  window.MandelbrotSet = new MandelbrotSet();