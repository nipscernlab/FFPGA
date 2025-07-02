/**
 * Controle do conteúdo educacional
 * Este script gerencia o conteúdo dinâmico da seção educativa
 */
document.addEventListener('DOMContentLoaded', () => {
    // Esta função pode ser expandida para carregar conteúdo dinamicamente
    // ou adicionar interatividade ao conteúdo educacional
    
    // Mostrar automaticamente o modal educativo na primeira execução
    const isFirstRun = !localStorage.getItem('mandelbrotExplorerVisited');
    
    if (isFirstRun) {
      // Mostrar o modal após um pequeno atraso para garantir
      // que tudo esteja carregado
      setTimeout(() => {
        document.getElementById('education-modal').classList.add('active');
        localStorage.setItem('mandelbrotExplorerVisited', 'true');
      }, 1000);
    }
    
    // Podemos adicionar mais funcionalidades aqui, como:
    // - Exibições interativas de conceitos
    // - Renderizações de exemplos simples
    // - Tutorial passo a passo
  });