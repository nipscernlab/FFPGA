// Controle de interface do usuário
document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos de UI
    const minimizeBtn = document.getElementById('minimize-btn');
    const maximizeBtn = document.getElementById('maximize-btn');
    const closeBtn = document.getElementById('close-btn');
    const educationBtn = document.getElementById('education-btn');
    const educationModal = document.getElementById('education-modal');
    const closeModalBtn = document.querySelector('.close-modal');
    const startExploringBtn = document.querySelector('.modal-btn.primary');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Controles do Electron para a janela
    minimizeBtn.addEventListener('click', () => {
      window.electronAPI.windowControl.minimize();
    });
    
    maximizeBtn.addEventListener('click', () => {
      window.electronAPI.windowControl.maximize();
    });
    
    closeBtn.addEventListener('click', () => {
      window.electronAPI.windowControl.quit();
    });
    
    // Controle do modal educativo
    educationBtn.addEventListener('click', () => {
      educationModal.classList.add('active');
    });
    
    closeModalBtn.addEventListener('click', () => {
      educationModal.classList.remove('active');
    });
    
    startExploringBtn.addEventListener('click', () => {
      educationModal.classList.remove('active');
    });
    
    // Fechar modal ao clicar fora do conteúdo
    educationModal.addEventListener('click', (e) => {
      if (e.target === educationModal) {
        educationModal.classList.remove('active');
      }
    });
    
    // Controle das abas do modal
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        // Remover classe active de todas as abas
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Adicionar classe active à aba clicada
        btn.classList.add('active');
        
        // Mostrar conteúdo da aba
        const tabId = btn.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
      });
    });
    
    // Controles do fractal
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const resetViewBtn = document.getElementById('reset-view-btn');
    const iterationsSlider = document.getElementById('iterations-slider');
    const iterationsValue = document.getElementById('iterations-value');
    const colorSchemeSelect = document.getElementById('color-scheme');
    
    zoomInBtn.addEventListener('click', () => {
      // Será implementado no fractal-renderer.js
      window.fractalApp.zoomIn();
    });
    
    zoomOutBtn.addEventListener('click', () => {
      window.fractalApp.zoomOut();
    });
    
    resetViewBtn.addEventListener('click', () => {
      window.fractalApp.resetView();
    });
    
    iterationsSlider.addEventListener('input', (e) => {
      const value = e.target.value;
      iterationsValue.textContent = value;
      window.fractalApp.setIterations(value);
    });
    
    colorSchemeSelect.addEventListener('change', (e) => {
      window.fractalApp.setColorScheme(e.target.value);
    });
    
    // Evento para redimensionamento da janela
    window.addEventListener('resize', () => {
      window.fractalApp.handleResize();
    });
  });