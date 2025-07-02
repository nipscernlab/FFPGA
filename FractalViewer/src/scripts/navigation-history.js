/**
 * Sistema de histórico de navegação pelo fractal
 * Permite que o usuário salve e retorne a posições interessantes
 */
class NavigationHistory {
    constructor(fractalRenderer) {
      this.renderer = fractalRenderer;
      this.history = [];
      this.currentIndex = -1;
      this.maxHistory = 10;
      
      // Elementos da UI
      this.historyList = document.getElementById('history-list');
      this.backBtn = document.getElementById('history-back');
      this.forwardBtn = document.getElementById('history-forward');
      this.savePositionBtn = document.getElementById('save-position');
      
      // Inicialização
      this.setupEventListeners();
      this.updateHistoryButtons();
    }
    
    setupEventListeners() {
      if (this.backBtn) {
        this.backBtn.addEventListener('click', () => this.goBack());
      }
      
      if (this.forwardBtn) {
        this.forwardBtn.addEventListener('click', () => this.goForward());
      }
      
      if (this.savePositionBtn) {
        this.savePositionBtn.addEventListener('click', () => this.saveCurrentPosition());
      }
    }
    
    saveCurrentPosition(name = '') {
      // Obter a posição atual do renderer
      const position = {
        viewportX: this.renderer.viewportX,
        viewportY: this.renderer.viewportY,
        viewportWidth: this.renderer.viewportWidth,
        viewportHeight: this.renderer.viewportHeight,
        zoom: this.renderer.zoom,
        timestamp: Date.now(),
        name: name || `Posição ${this.history.length + 1}`
      };
      
      // Remover entradas futuras se estivemos no meio do histórico
      if (this.currentIndex < this.history.length - 1) {
        this.history = this.history.slice(0, this.currentIndex + 1);
      }
      
      // Adicionar a nova posição ao histórico
      this.history.push(position);
      this.currentIndex = this.history.length - 1;
      
      // Manter o histórico dentro do limite
      if (this.history.length > this.maxHistory) {
        this.history.shift();
        this.currentIndex--;
      }
      
      this.updateHistoryButtons();
      this.updateHistoryList();
    }
    
    goBack() {
      if (this.currentIndex > 0) {
        this.currentIndex--;
        this.goToPosition(this.history[this.currentIndex]);
        this.updateHistoryButtons();
      }
    }
    
    goForward() {
      if (this.currentIndex < this.history.length - 1) {
        this.currentIndex++;
        this.goToPosition(this.history[this.currentIndex]);
        this.updateHistoryButtons();
      }
    }
    
    goToPosition(position) {
      this.renderer.viewportX = position.viewportX;
      this.renderer.viewportY = position.viewportY;
      this.renderer.viewportWidth = position.viewportWidth;
      this.renderer.viewportHeight = position.viewportHeight;
      this.renderer.zoom = position.zoom;
      
      this.renderer.zoomLevel.textContent = `Zoom: ${position.zoom.toFixed(1)}x`;
      this.renderer.render();
    }
    
    goToIndex(index) {
      if (index >= 0 && index < this.history.length) {
        this.currentIndex = index;
        this.goToPosition(this.history[index]);
        this.updateHistoryButtons();
      }
    }
    
    updateHistoryButtons() {
      if (this.backBtn) {
        this.backBtn.disabled = this.currentIndex <= 0;
      }
      
      if (this.forwardBtn) {
        this.forwardBtn.disabled = this.currentIndex >= this.history.length - 1;
      }
    }
    
    updateHistoryList() {
      if (!this.historyList) return;
      
      // Limpar a lista existente
      this.historyList.innerHTML = '';
      
      // Adicionar cada posição à lista
      this.history.forEach((position, index) => {
        const item = document.createElement('div');
        item.className = 'history-item';
        if (index === this.currentIndex) {
          item.classList.add('active');
        }
        
        item.innerHTML = `
          <span class="history-name">${position.name}</span>
          <span class="history-coords">
            (${position.viewportX.toFixed(3)}, ${position.viewportY.toFixed(3)})
            ${position.zoom.toFixed(1)}x
          </span>
        `;
        
        item.addEventListener('click', () => this.goToIndex(index));
        this.historyList.appendChild(item);
      });
    }
  }
  
  // Inicializar quando a página carregar
  document.addEventListener('DOMContentLoaded', () => {
    // Esperar o fractalApp ser inicializado
    setTimeout(() => {
      if (window.fractalApp) {
        window.navigationHistory = new NavigationHistory(window.fractalApp);
      }
    }, 500);
  });