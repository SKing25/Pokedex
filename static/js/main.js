// ===== FUNCIONES GLOBALES =====

// IvAn


    const chatButton = document.getElementById('open-chat-btn');
    const closeButton = document.getElementById('close-chat-btn');
    const chatContainer = document.getElementById('ivan-chat-container');
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');

    chatButton.addEventListener('click', () => {
        chatContainer.style.display = 'flex';
        chatButton.style.display = 'none';
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    closeButton.addEventListener('click', () => {
        chatContainer.style.display = 'none';
        chatButton.style.display = 'block';
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // Mostrar el mensaje del usuario
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('chat-message', 'user-message');
        userMessageDiv.textContent = message;
        chatBox.appendChild(userMessageDiv);
        
        userInput.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;

        // Enviar el mensaje al servidor Flask
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Mostrar la respuesta de la IA
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.classList.add('chat-message', 'ai-message');
            aiMessageDiv.innerHTML = data.response; // Usar innerHTML para interpretar los enlaces
            chatBox.appendChild(aiMessageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch((error) => {
            console.error('Error:', error);
            const errorMessageDiv = document.createElement('div');
            errorMessageDiv.classList.add('chat-message', 'ai-message');
            errorMessageDiv.textContent = 'Lo siento, hubo un error. Por favor, inténtalo de nuevo más tarde.';
            chatBox.appendChild(errorMessageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }


// Función para toggle de modo oscuro con lógica mejorada
function toggleDarkMode() {
    const body = document.body;
    const toggleButton = document.querySelector('.dark-mode-toggle');
    
    body.classList.toggle('dark-mode');
    
    // Actualizar texto del botón según el estado actual
    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('darkMode', 'enabled');
        toggleButton.textContent = 'Modo Claro';
    } else {
        localStorage.setItem('darkMode', 'disabled');
        toggleButton.textContent = 'Modo Oscuro';
    }
}

// Inicializar modo oscuro al cargar la página
function initializeDarkMode() {
    const toggleButton = document.querySelector('.dark-mode-toggle');
    
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        toggleButton.textContent = 'Modo Claro';
    } else {
        toggleButton.textContent = 'Modo Oscuro';
    }
}

// ===== FUNCIONES ESPECÍFICAS PARA PÁGINAS =====

// Scripts específicos para index.html
function initializeIndexPage() {
    const sprites = document.querySelectorAll('.floating-sprite');
    
    // Animación escalonada de sprites
    sprites.forEach((sprite, index) => {
        sprite.style.animationDelay = `${index * 0.5}s`;
        
        setTimeout(() => {
            sprite.classList.add('sprite-loaded');
        }, index * 200);
    });

    // View Transitions API para enlaces
    if ('startViewTransition' in document) {
        const allLinks = document.querySelectorAll('.pokemon-card-link, #to_pokedex');
        
        allLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const href = this.href;
                
                document.startViewTransition(() => {
                    window.location.href = href;
                });
            });
        });
    }

    // Efecto hover mejorado para las cartas
    const pokemonCards = document.querySelectorAll('.carousel-pokemon');
    pokemonCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.05)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Manejar clicks en enlaces de Pokémon con transiciones
    document.querySelectorAll('a[href^="/pokedex"]').forEach(link => {
        link.addEventListener('click', async (e) => {
            if (!document.startViewTransition) {
                return; // Navegación normal si no hay soporte
            }
            
            e.preventDefault();
            
            // Iniciar transición
            const transition = document.startViewTransition(async () => {
                await fetch(link.href); // Precargar contenido
                location.href = link.href;
            });
            
            // Manejar posible cancelación
            transition.ready.catch(() => {
                location.href = link.href; // Fallback si se cancela
            });
        });
    });
}

// Scripts específicos para pokemon.html
function initializePokemonDetailPage() {
    // Variables globales para mantener el estado
    window.currentShiny = typeof pokemon_data !== 'undefined' ? pokemon_data.current_shiny : false;
    window.currentGender = typeof pokemon_data !== 'undefined' ? pokemon_data.current_gender : 'male';

    // Función para actualizar botones activos
    window.updateActiveButtons = function(clickedButton, containerId, newValue) {
        // Actualizar estado global
        if (containerId === 'shiny-controls') {
            window.currentShiny = newValue;
        } else if (containerId === 'gender-controls') {
            window.currentGender = newValue;
        }

        // Remover clase active de todos los botones en el contenedor
        const container = document.getElementById(containerId);
        const buttons = container.querySelectorAll('.toggle-button');
        buttons.forEach(btn => btn.classList.remove('active'));
        
        // Agregar clase active al botón clickeado
        clickedButton.classList.add('active');

        // Actualizar los URLs de los otros botones para mantener consistencia
        updateButtonUrls();
    };

    // Función para actualizar URLs de botones
    function updateButtonUrls() {
        const pokemonName = typeof pokemon_data !== 'undefined' ? pokemon_data.name.toLowerCase() : '';
        
        // Actualizar botones de shiny
        const shinyContainer = document.getElementById('shiny-controls');
        if (shinyContainer) {
            const buttons = shinyContainer.querySelectorAll('.toggle-button');
            buttons.forEach(btn => {
                const isShiny = btn.getAttribute('data-shiny') === 'true';
                btn.setAttribute('hx-get', `/sprite/${pokemonName}?shiny=${isShiny}&gender=${window.currentGender}`);
            });
        }

        // Actualizar botones de género si existen
        const genderContainer = document.getElementById('gender-controls');
        if (genderContainer) {
            const buttons = genderContainer.querySelectorAll('.toggle-button');
            buttons.forEach(btn => {
                const gender = btn.getAttribute('data-gender');
                btn.setAttribute('hx-get', `/sprite/${pokemonName}?shiny=${window.currentShiny}&gender=${gender}`);
            });
        }
    }

    // Event listeners para HTMX
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (typeof htmx !== 'undefined') {
            htmx.process(event.target);
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.status === 200) {
            console.log('Sprite actualizado correctamente');
        }
    });
}

// ===== INICIALIZACIÓN GENERAL =====

// Detectar página actual e inicializar funciones específicas
function initializePage() {
    initializeDarkMode();
    
    // Detectar página actual basándose en elementos únicos
    if (document.querySelector('.index-container')) {
        // Página de inicio
        initializeIndexPage();
    } else if (document.querySelector('.pokemon-detail-container')) {
        // Página de detalle de Pokémon
        initializePokemonDetailPage();
    }
    // Para pokedex.html no hay inicialización específica adicional
}






// Ejecutar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initializePage);