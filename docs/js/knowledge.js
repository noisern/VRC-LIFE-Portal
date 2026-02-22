const DATA_URL = '../data/knowledge.json';

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('knowledge-grid');
    const searchInput = document.getElementById('search-input');
    
    let allArticles = [];
    let currentCategory = 'all';

    async function init() {
        try {
            const response = await fetch(DATA_URL);
            if (!response.ok) throw new Error('Failed to fetch knowledge data');
            
            allArticles = await response.json();
            
            // Render
            renderArticles(allArticles);
            
            // Filters
            initFilters();
            
        } catch(e) {
            console.error(e);
            if (grid) {
                grid.innerHTML = '<div class="col-span-full text-center py-20 text-[#999999]">Failed to load articles.</div>';
            }
        }
    }

    // Initial load
    init();

    function renderArticles(articles) {
        if (!grid) return;
        grid.innerHTML = '';

        if (articles.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center py-20 text-[#999999]">No articles found matching your criteria.</div>';
            return;
        }

        articles.forEach(article => {
            const card = document.createElement('a');
            // We use JS dynamic routing or a generic article.html?id=xyz
            // For now, if "article01.html" is hardcoded, we can use it, else point to article.html
            // The prompt says "id: 1" should be parsed and reflected.
            card.href = `article.html?id=${article.id}`;
            card.className = 'group block bg-white border border-[#E5E4DE] overflow-hidden hover:border-[#999999] hover:shadow-lg transition-all duration-300 relative';

            // Category Badge Color
            let categoryClass = 'bg-[#F0F0F0] text-[#666666]';
            if (article.category === 'VRC START GUIDE' || article.category === 'VRChat入門') categoryClass = 'bg-blue-50 text-blue-600 border border-blue-100';
            if (article.category === 'UNITY BASICS' || article.category === '改変基礎') categoryClass = 'bg-green-50 text-green-600 border border-green-100';
            if (article.category === 'TROUBLESHOOTING' || article.category === 'トラブル解決') categoryClass = 'bg-red-50 text-red-600 border border-red-100';

            // Add number overlay if it's chapter-based (heuristic: if title contains start, or category is intro)
            let isIntro = categoryClass.includes('blue');
            let numberOverlay = '';
            if (isIntro) {
                // simple hack to get a number if not provided, just index based or id based
                let num = String(article.id).padStart(2, '0');
                numberOverlay = `
                    <div class="absolute top-0 right-2 text-7xl font-thin text-white/40 select-none z-10 transition-colors group-hover:text-white/60">
                        ${num}
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="aspect-[16/9] overflow-hidden relative bg-[#E5E4DE]">
                    <img src="${article.thumbnail_url || article.image_url || '../images/logo.png'}" alt="${article.title}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105">
                    ${numberOverlay}
                </div>
                <div class="p-6 relative z-20">
                    <div class="mb-4">
                        <span class="text-[10px] uppercase tracking-widest px-2 py-1 rounded-sm ${categoryClass}">
                            ${article.category}
                        </span>
                    </div>
                    <!-- Playfair Display for title aesthetic -->
                    <h3 class="text-xl font-serif-display font-light text-[#333333] mb-1 group-hover:text-black transition-colors leading-relaxed tracking-wide" style="font-family: 'Playfair Display', serif;">${article.title}</h3>
                    <p class="text-[10px] text-[#999] font-medium tracking-wider mb-3 uppercase">${article.subtitle || ''}</p>
                    <p class="text-sm text-[#666666] line-clamp-3 leading-relaxed font-light">${article.excerpt || article.summary || ''}</p>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    function initFilters() {
        const banners = document.querySelectorAll('.category-banner');
        banners.forEach(banner => {
            banner.addEventListener('click', () => {
                currentCategory = banner.getAttribute('data-category');

                filterArticles(currentCategory, searchInput ? searchInput.value : '');

                // Smooth scroll to grid
                if (grid) {
                    const yOffset = -100; // offset for sticky header
                    const y = grid.getBoundingClientRect().top + window.pageYOffset + yOffset;
                    window.scrollTo({top: y, behavior: 'smooth'});
                }
            });
        });

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value;
                filterArticles(currentCategory, query);
            });
        }
    }

    function filterArticles(category, query) {
        const lowerQuery = query.toLowerCase();

        const filtered = allArticles.filter(article => {
            // Fuzzy category match to support both JA/EN names based on the layout
            const cCategory = article.category || '';
            let matchesCategory = false;
            if (category === 'all') matchesCategory = true;
            else if (category === 'VRChat入門' && (cCategory.includes('VRC') || cCategory.includes('入門'))) matchesCategory = true;
            else if (category === '改変基礎' && (cCategory.includes('UNITY') || cCategory.includes('改変'))) matchesCategory = true;
            else if (category === 'トラブル解決' && (cCategory.includes('TROUBLE') || cCategory.includes('解決'))) matchesCategory = true;
            else matchesCategory = cCategory === category;

            const matchesSearch = 
                (article.title || '').toLowerCase().includes(lowerQuery) ||
                (article.excerpt || article.summary || '').toLowerCase().includes(lowerQuery) ||
                (article.tags || []).some(t => t.toLowerCase().includes(lowerQuery));

            return matchesCategory && matchesSearch;
        });

        renderArticles(filtered);
    }
});
