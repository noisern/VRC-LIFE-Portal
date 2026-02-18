document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('worlds-grid');
    const filterBtns = document.querySelectorAll('.filter-btn');
    let allWorlds = [];

    // Fetch data from JSON
    fetch('data/worlds.json')
        .then(response => response.json())
        .then(data => {
            allWorlds = data;
            renderWorlds(allWorlds);
        })
        .catch(error => {
            console.error('Error fetching worlds:', error);
            grid.innerHTML = '<div class="col-span-full text-center py-10 text-red-500">Failed to load world data.</div>';
        });

    // Render worlds function
    function renderWorlds(worlds) {
        grid.innerHTML = '';
        
        if (worlds.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center py-20 text-gray-400">No worlds found matching this filter.</div>';
            return;
        }

        worlds.forEach(world => {
            const card = document.createElement('div');
            card.className = 'group bg-white border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow duration-300';
            
            // Format tags for display
            const tagsHtml = world.tags.map(tag => `<span class="text-[10px] uppercase tracking-wider text-gray-500 bg-gray-50 px-2 py-1 rounded-sm">#${tag}</span>`).join(' ');

            card.innerHTML = `
                <div class="aspect-video overflow-hidden bg-gray-200 relative">
                    <img src="${world.image}" alt="${world.name}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 filter grayscale group-hover:grayscale-0">
                    <div class="absolute inset-0 bg-black/5 group-hover:bg-transparent transition-colors"></div>
                </div>
                <div class="p-5">
                    <div class="flex flex-wrap gap-2 mb-3">
                        ${tagsHtml}
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">${world.name}</h3>
                    <p class="text-xs text-gray-400 mb-3">by ${world.author}</p>
                    <p class="text-sm text-gray-600 line-clamp-2 leading-relaxed font-light">${world.description}</p>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Filter Logic
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => {
                b.classList.remove('bg-black', 'text-white');
                b.classList.add('bg-white', 'text-gray-600');
            });
            btn.classList.remove('bg-white', 'text-gray-600');
            btn.classList.add('bg-black', 'text-white');

            const tag = btn.getAttribute('data-tag');
            
            if (tag === 'all') {
                renderWorlds(allWorlds);
            } else {
                const filtered = allWorlds.filter(world => world.tags.includes(tag));
                renderWorlds(filtered);
            }
        });
    });
});
