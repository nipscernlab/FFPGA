# Visualizador de Fractais - Projeto Electron

Este projeto é um aplicativo educativo sobre fractais, com foco no conjunto de Mandelbrot.
Vou organizar o projeto com a seguinte estrutura:

1. Estrutura de pastas
2. Arquivos principais
3. Componentes e módulos
4. Estilos
5. Scripts

## Estrutura de Pastas

```
mandelbrot-explorer/
├── package.json
├── main.js
├── preload.js
├── index.html
├── src/
│   ├── styles/
│   │   ├── main.css
│   │   ├── variables.css
│   │   └── modal.css
│   ├── scripts/
│   │   ├── fractal-renderer.js
│   │   ├── mandelbrot.js
│   │   ├── ui-controller.js
│   │   └── education-content.js
│   └── components/
│       ├── fractal-viewer.js
│       └── education-modal.js
├── assets/
│   ├── icons/
│   │   ├── zoom-in.svg
│   │   ├── zoom-out.svg
│   │   ├── info.svg
│   │   ├── app-icon.png
│   │   └── reset.svg
│   └── images/
│       └── mandelbrot-example.png
└── README.md
```

## package.json