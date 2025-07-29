let isShiny = false;
        let currentGender = 'male';


        
        const spriteData = {
            front_default: "{{ pokemon_data.sprites.front_default or '' }}",
            front_shiny: "{{ pokemon_data.sprites.front_shiny or '' }}",
            front_female: "{{ pokemon_data.sprites.front_female or '' }}",
            front_shiny_female: "{{ pokemon_data.sprites.front_shiny_female or '' }}"
        };

        function updateSprite() {
            const sprite = document.getElementById('pokemonSprite');
            const spriteInfo = document.getElementById('spriteInfo');

            let newSrc = '';
            let infoText = '';

// ESTA MONDA NO FUNCIONA AAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            if (isShiny && currentGender === 'female' && spriteData.front_shiny_female) {
                newSrc = pokemon_data.sprites.front_shiny_female;
                infoText = 'Shiny - Hembra';
            } else if (isShiny && spriteData.front_shiny) {
                newSrc = pokemon_data.sprites.front_shiny;
                infoText = 'Shiny - Macho';
            } else if (!isShiny && currentGender === 'female' && spriteData.front_female) {
                newSrc = pokemon_data.sprites.front_female;
                infoText = 'Normal - Hembra';
            } else if (spriteData.front_default) { 
                newSrc = pokemon_data.sprites.front_default ;
                infoText = 'Normal - Macho';
            }

            
            if (!newSrc) {
                sprite.style.display = 'none';
                spriteInfo.innerHTML = '<div class="sprite-not-available">Sprite no disponible</div>';
                return;
            }

            
            if (newSrc !== sprite.src) {
                sprite.classList.add('changing');

                setTimeout(() => {
                    sprite.src = newSrc;
                    sprite.classList.remove('changing');
                    sprite.classList.add('loaded');
                    spriteInfo.textContent = infoText;
                    sprite.style.display = 'block'; // Ensure sprite is visible
                }, 200);
            } else {
            
                spriteInfo.textContent = infoText;
                sprite.style.display = 'block';
            }
        }

        function toggleShiny(shiny) {
            isShiny = shiny;


            document.getElementById('normalBtn').classList.toggle('active', !shiny);
            document.getElementById('shinyBtn').classList.toggle('active', shiny);

            updateSprite();
        }

        function toggleGender(gender) {
            currentGender = gender;


            const maleBtn = document.getElementById('maleBtn');
            const femaleBtn = document.getElementById('femaleBtn');

            if (maleBtn && femaleBtn) {
                maleBtn.classList.toggle('active', gender === 'male');
                femaleBtn.classList.toggle('active', gender === 'female');
            }

            updateSprite();
        }


        document.addEventListener('DOMContentLoaded', function() {
            const normalBtn = document.getElementById('normalBtn');
            const maleBtn = document.getElementById('maleBtn');
            const femaleBtn = document.getElementById('femaleBtn');


            if (normalBtn) {
                normalBtn.classList.add('active');
            }
            if (maleBtn) {
                maleBtn.classList.add('active');
            }


            const backButton = document.querySelector('.back-button');
            if (backButton) {
                backButton.addEventListener('click', function(e) {
                    if ('startViewTransition' in document) {
                        e.preventDefault();
                        document.startViewTransition(() => {
                            window.location.href = this.href;
                        });
                    }
                });
            }
        });