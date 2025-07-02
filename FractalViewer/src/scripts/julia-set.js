/**
 * Classe para cálculos relacionados ao conjunto de Julia
 */
class JuliaSet {
    constructor() {
      // Valores padrão
      this.maxIterations = 100;
      this.escapeRadius = 2;
      this.escapeRadiusSq = this.escapeRadius * this.escapeRadius;
      
      // Parâmetro c para o conjunto de Julia
      this.cReal = -0.7;
      this.cImag = 0.27015;
    }
    
    /**
     * Calcula se um ponto pertence ao conjunto de Julia
     * @param {number} x - Coordenada real
     * @param {number} y - Coordenada imaginária
     * @returns {number} Número de iterações até escapar (ou maxIterations)
     */
    computePoint(x, y) {
      // Implementação do algoritmo do conjunto de Julia
      // z = z² + c, onde c é um parâmetro fixo e z começa com o ponto (x, y)
      let real = x;
      let imag = y;
      let iteration = 0;
      
      while (iteration < this.maxIterations) {
        // z² = (a + bi)² = a² - b² + 2abi
        const realSquared = real * real;
        const imagSquared = imag * imag;
        
        // Verificar se o ponto escapou
        if (realSquared + imagSquared > this.escapeRadiusSq) {
          break;
        }
        
        // z = z² + c
        const realTemp = realSquared - imagSquared + this.cReal;
        imag = 2 * real * imag + this.cImag;
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
    
    /**
     * Define o parâmetro c para o conjunto de Julia
     * @param {number} real - Parte real de c
     * @param {number} imag - Parte imaginária de c
     */
    setParameter(real, imag) {
      this.cReal = real;
      this.cImag = imag;
    }
  }
  
  // Criar objeto global para acessar em outros scripts
  window.JuliaSet = new JuliaSet();