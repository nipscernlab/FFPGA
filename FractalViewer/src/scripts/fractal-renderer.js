/**
 * Classe para renderização do fractal no canvas
 */
class FractalRenderer {
  constructor() {
    // Referências de elementos
    this.canvas = document.getElementById('fractal-canvas');
    this.ctx = this.canvas.getContext('2d');
    this.mouseCoords = document.getElementById('mouse-coords');
    this.zoomLevel = document.getElementById('zoom-level');
    
    // Configuração inicial
    this.mandelbrot = window.MandelbrotSet;
    this.viewportX = -2.5;      // Posição X do canto superior esquerdo
    this.viewportY = -1.5;      // Posição Y do canto superior esquerdo
    this.viewportWidth = 4.0;   // Largura do viewport no plano complexo
    this.zoom = 1.0;            // Fator de zoom atual
    this.isDragging = false;    // Flag para o arrastar
    this.lastX = 0;             // Última posição X do mouse
    this.lastY = 0;             // Última posição Y do mouse
    this.colorScheme = 'rainbow'; // Esquema de cores padrão
    
    // Inicialização
    this.setupCanvas();
    this.setupEventListeners();
    this.render();
  }
  
  /**
   * Configura o canvas para o tamanho correto
   */
  setupCanvas() {
    // Ajustar o canvas para o tamanho correto (DPI)
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    
    // Calcular proporção para manter o aspecto correto
    const aspectRatio = this.canvas.width / this.canvas.height;
    this.viewportHeight = this.viewportWidth / aspectRatio;
  }
  
  /**
   * Configura os eventos de mouse e toque
   */
  setupEventListeners() {
    // Eventos de mouse
    this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
    this.canvas.addEventListener('wheel', this.handleWheel.bind(this));
    
    // Eventos de toque
    this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
    this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
    this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
  }
  
  /**
   * Converte coordenadas do canvas para o plano complexo
   */
  canvasToComplex(x, y) {
    const real = this.viewportX + (x / this.canvas.width) * this.viewportWidth;
    const imag = this.viewportY + (y / this.canvas.height) * this.viewportHeight;
    return { real, imag };
  }
  
  /**
   * Manipulador de evento de pressionar o mouse
   */
  handleMouseDown(e) {
    this.isDragging = true;
    this.lastX = e.clientX;
    this.lastY = e.clientY;
    this.canvas.style.cursor = 'grabbing';
  }
  
  /**
   * Manipulador de evento de mover o mouse
   */
  handleMouseMove(e) {
    // Atualizar coordenadas do mouse
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const complex = this.canvasToComplex(x, y);
    this.mouseCoords.textContent = `X: ${complex.real.toFixed(6)}, Y: ${complex.imag.toFixed(6)}`;
    
    // Se estiver arrastando, mover o viewport
    if (this.isDragging) {
      const deltaX = e.clientX - this.lastX;
      const deltaY = e.clientY - this.lastY;
      
      // Ajustar o deslocamento com base no zoom
      const moveX = (deltaX / this.canvas.width) * this.viewportWidth;
      const moveY = (deltaY / this.canvas.height) * this.viewportHeight;
      
      // Mover o viewport na direção oposta
      this.viewportX -= moveX;
      this.viewportY -= moveY;
      
      this.lastX = e.clientX;
      this.lastY = e.clientY;
      this.render();
    }
  }
  
  /**
   * Manipulador de evento de soltar o mouse
   */
  handleMouseUp() {
    this.isDragging = false;
    this.canvas.style.cursor = 'crosshair';
  }
  
  /**
   * Manipulador de evento de roda do mouse (zoom)
   */
  handleWheel(e) {
    e.preventDefault();
    
    // Calcular o ponto sob o ponteiro do mouse
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const complex = this.canvasToComplex(x, y);
    
    // Fator de zoom
    const zoomFactor = e.deltaY < 0 ? 0.8 : 1.25;
    
    // Ajustar zoom
    const oldWidth = this.viewportWidth;
    const oldHeight = this.viewportHeight;
    this.viewportWidth *= zoomFactor;
    this.viewportHeight *= zoomFactor;
    
    // Ajustar a posição para manter o ponto sob o cursor
    this.viewportX = complex.real - (complex.real - this.viewportX) * (this.viewportWidth / oldWidth);
    this.viewportY = complex.imag - (complex.imag - this.viewportY) * (this.viewportHeight / oldHeight);
    
    // Atualizar zoom atual
    this.zoom *= (1 / zoomFactor);
    this.zoomLevel.textContent = `Zoom: ${this.zoom.toFixed(1)}x`;
    
    this.render();
  }
  
  /**
   * Manipulador de evento de início de toque
   */
  handleTouchStart(e) {
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      this.lastX = touch.clientX;
      this.lastY = touch.clientY;
      this.isDragging = true;
    }
  }
  
  /**
   * Manipulador de evento de movimento de toque
   */
  handleTouchMove(e) {
    e.preventDefault();
    if (!this.isDragging) return;
    
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      const deltaX = touch.clientX - this.lastX;
      const deltaY = touch.clientY - this.lastY;
      
      // Ajustar o deslocamento com base no zoom
      const moveX = (deltaX / this.canvas.width) * this.viewportWidth;
      const moveY = (deltaY / this.canvas.height) * this.viewportHeight;
      
      // Mover o viewport na direção oposta
      this.viewportX -= moveX;
      this.viewportY -= moveY;
      
      this.lastX = touch.clientX;
      this.lastY = touch.clientY;
      this.render();
    }
  }
  
  /**
   * Manipulador de evento de fim de toque
   */
  handleTouchEnd() {
    this.isDragging = false;
  }
  
  /**
   * Renderiza o fractal
   */
  render() {
    // Criar imageData para manipulação direta de pixels
    const imageData = this.ctx.createImageData(this.canvas.width, this.canvas.height);
    const data = imageData.data;
    
    // Para cada pixel
    for (let y = 0; y < this.canvas.height; y++) {
      for (let x = 0; x < this.canvas.width; x++) {
        // Converter coordenadas do canvas para plano complexo
        const complex = this.canvasToComplex(x, y);
        
        // Calcular o valor do conjunto de Mandelbrot
        const value = this.mandelbrot.computePoint(complex.real, complex.imag);
        
        // Calcular o índice do pixel no array de dados
        const pixelIndex = (y * this.canvas.width + x) * 4;
        
        // Colorir o pixel com base no valor
        this.colorPixel(data, pixelIndex, value);
      }
    }
    
    // Desenhar a imagem no canvas
    this.ctx.putImageData(imageData, 0, 0);
  }
  
  /**
   * Colore um pixel com base no esquema de cores
   */
  colorPixel(data, index, value) {
    // Se o valor for igual ao máximo de iterações, é preto (pertence ao conjunto)
    if (value === this.mandelbrot.maxIterations) {
      data[index] = 0;     // R
      data[index + 1] = 0; // G
      data[index + 2] = 0; // B
      data[index + 3] = 255; // A
      return;
    }
    
    // Normalizar o valor para o intervalo [0, 1]
    const normalized = value / this.mandelbrot.maxIterations;
    
    // Aplicar o esquema de cores
    let r, g, b;
    
    switch (this.colorScheme) {
      case 'rainbow':
        // Esquema de cores arco-íris
        const hue = 360 * normalized;
        [r, g, b] = this.hslToRgb(hue, 0.8, 0.5);
        break;
      
      case 'purpleblue':
        // Esquema de cores roxo-azul
        const blueHue = 240 + 60 * normalized;
        [r, g, b] = this.hslToRgb(blueHue % 360, 0.7, 0.5);
        break;
      
      case 'fire':
        // Esquema de cores fogo
        const fireHue = 30 - 30 * normalized;
        const fireSat = 0.8 + normalized * 0.2;
        const fireLum = normalized * 0.5;
        [r, g, b] = this.hslToRgb(fireHue, fireSat, fireLum);
        break;
      
      case 'electric':
        // Esquema de cores elétrico
        const elecHue = 180 + 180 * normalized;
        const elecSat = 0.8;
        const elecLum = 0.2 + normalized * 0.5;
        [r, g, b] = this.hslToRgb(elecHue % 360, elecSat, elecLum);
        break;
      
      case 'grayscale':
        // Escala de cinza
        r = g = b = Math.round(normalized * 255);
        break;
        
      default:
        // Esquema padrão
        r = Math.round(255 * Math.sin(normalized * Math.PI));
        g = Math.round(255 * Math.sin(normalized * Math.PI * 2));
        b = Math.round(255 * Math.sin(normalized * Math.PI * 3));
    }
    
    // Definir os valores RGBA
    data[index] = r;     // R
    data[index + 1] = g; // G
    data[index + 2] = b; // B
    data[index + 3] = 255; // A
  }
  
  /**
   * Converte HSL para RGB
   * H: [0, 360], S: [0, 1], L: [0, 1]
   */
  hslToRgb(h, s, l) {
    h /= 360;
    let r, g, b;

    if (s === 0) {
      r = g = b = l; // acromático
    } else {
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };

      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }

    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
  }
  
  /**
   * Métodos públicos para interação com UI
   */
  zoomIn() {
    // Zoom no centro
    const centerX = this.viewportX + this.viewportWidth / 2;
    const centerY = this.viewportY + this.viewportHeight / 2;
    
    // Fator de zoom
    const zoomFactor = 0.5;
    
    // Ajustar zoom
    this.viewportWidth *= zoomFactor;
    this.viewportHeight *= zoomFactor;
    
    // Ajustar posição para manter o centro
    this.viewportX = centerX - this.viewportWidth / 2;
    this.viewportY = centerY - this.viewportHeight / 2;
    
    // Atualizar zoom atual
    this.zoom *= 2;
    this.zoomLevel.textContent = `Zoom: ${this.zoom.toFixed(1)}x`;
    
    this.render();
  }
  
  zoomOut() {
    // Zoom no centro
    const centerX = this.viewportX + this.viewportWidth / 2;
    const centerY = this.viewportY + this.viewportHeight / 2;
    
    // Fator de zoom
    const zoomFactor = 2.0;
    
    // Ajustar zoom
    this.viewportWidth *= zoomFactor;
    this.viewportHeight *= zoomFactor;
    
    // Ajustar posição para manter o centro
    this.viewportX = centerX - this.viewportWidth / 2;
    this.viewportY = centerY - this.viewportHeight / 2;
    
    // Atualizar zoom atual
    this.zoom /= 2;
    this.zoomLevel.textContent = `Zoom: ${this.zoom.toFixed(1)}x`;
    
    this.render();
  }
  
  resetView() {
    // Resetar para vista padrão
    this.viewportX = -2.5;
    this.viewportY = -1.5;
    this.viewportWidth = 4.0;
    
    // Recalcular altura com base no aspecto
    const aspectRatio = this.canvas.width / this.canvas.height;
    this.viewportHeight = this.viewportWidth / aspectRatio;
    
    // Resetar zoom
    this.zoom = 1.0;
    this.zoomLevel.textContent = `Zoom: ${this.zoom.toFixed(1)}x`;
    
    this.render();
  }
  
  setIterations(value) {
    this.mandelbrot.setMaxIterations(parseInt(value));
    this.render();
  }
  
  setColorScheme(scheme) {
    this.colorScheme = scheme;
    this.render();
  }
  
  handleResize() {
    // Salvar centro atual
    const centerX = this.viewportX + this.viewportWidth / 2;
    const centerY = this.viewportY + this.viewportHeight / 2;
    
    // Reconfigurar canvas
    this.setupCanvas();
    
    // Restaurar centro
    this.viewportX = centerX - this.viewportWidth / 2;
    this.viewportY = centerY - this.viewportHeight / 2;
    
    this.render();
  }
}

// Inicializar o renderizador quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
  // Criar objeto global para acesso em UI
  window.fractalApp = new FractalRenderer();
});