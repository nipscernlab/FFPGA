/**
 * Catálogo de locais interessantes no conjunto de Mandelbrot
 * para fins educacionais
 */
class InterestingLocations {
    constructor(fractalRenderer) {
      this.renderer = fractalRenderer;
      this.locations = [
        {
          name: "Conjunto Completo",
          description: "Visão geral do conjunto de Mandelbrot",
          x: -0.75,
          y: 0,
          width: 3.5,
          zoom: 1
        },
        {
          name: "Vale dos Elefantes",
          description: "Formação que lembra elefantes, situada na borda do conjunto principal",
          x: 0.275,
          y: 0,
          width: 0.15,
          zoom: 23.33
        },
        {
          name: "Mini Mandelbrot",
          description: "Uma cópia em miniatura do conjunto principal",
          x: -1.75,
          y: 0,
          width: 0.25,
          zoom: 14
        },
        {
          name: "Espiral Dupla",
          description: "Formação em espiral dupla, mostrando a auto-similaridade do conjunto",
          x: -0.745,
          y: 0.11,
          width: 0.01,
          zoom: 350
        },
        {
          name: "Vale de Seahorse",
          description: "Área com formato de cavalos-marinhos",
          x: -0.748,
          y: -0.08,
          width: 0.01,
          zoom: 350
        },
        {
          name: "Filamentos de Dendrita",
          description: "Estruturas que se ramificam como dendritos de neurônios",
          x: -0.235125,
          y: 0.827215,
          width: 0.00008,
          zoom: 43750
        }
      ];
      
      // Inicialização
      this.setupLocationsList();
    }
    
    setupLocationsList() {
      const locationsList = document.getElementById('locations-list');
      if (!locationsList) return;
      
      this.locations.forEach((location, index) => {
        const item = document.createElement('div');
        item.className = 'location-item';
        
        item.innerHTML = `
          <div class="location-header">
            <span class="location-name">${location.name}</span>
            <button class="location-goto-btn" data-index="${index}">
              <i class="fa-solid fa-arrow-right"></i>
            </button>
          </div>
          <span class="location-description">${location.description}</span>
        `;
        
        locationsList.appendChild(item);
        
        // Adicionar evento para ir para localização
        const gotoBtn = item.querySelector('.location-goto-btn');
        gotoBtn.addEventListener('click', () => this.goToLocation(index));
      });
    }
    
    goToLocation(index) {
      const location = this.locations[index];
      if (!location) return;
      
      // Calcular a altura com base na largura e proporção do canvas
      const aspectRatio = this.renderer.canvas.width / this.renderer.canvas.height;
      const height = location.width / aspectRatio;
      
      // Definir a viewport
      this.renderer.viewportX = location.x - location.width / 2;
      this.renderer.viewportY = location.y - height / 2;
      this.renderer.viewportWidth = location.width;
      this.renderer.viewportHeight = height;
      this.renderer.zoom = location.zoom;
      
      // Atualizar a UI
      this.renderer.zoomLevel.textContent = `Zoom: ${location.zoom.toFixed(1)}x`;
      
      // Renderizar o fractal
      this.renderer.render();
      
      // Se houver histórico, salvar esta posição
      if (window.navigationHistory) {
        window.navigationHistory.saveCurrentPosition(location.name);
      }
    }
  }
  
  // Inicializar quando a página carregar
  document.addEventListener('DOMContentLoaded', () => {
    // Esperar o fractalApp ser inicializado
    setTimeout(() => {
      if (window.fractalApp) {
        window.interestingLocations = new InterestingLocations(window.fractalApp);
      }
    }, 500);
  });