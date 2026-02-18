/**
 * VRC-LIFE Portal Fashion - Dynamic Item System
 *
 * items.json からアイテムデータを読み込み、
 * NEW ARRIVALS（index.html）と ITEM LIST（list.html）に動的表示する。
 */

document.addEventListener('DOMContentLoaded', () => {

    // === NEW ARRIVALS (index.html) ===
    const newArrivalsGrid = document.getElementById('new-arrivals-grid');
    if (newArrivalsGrid) {
        loadNewArrivals(newArrivalsGrid);
    }

    // === ITEM LIST (list.html) ===
    const itemGrid = document.getElementById('item-grid');
    if (itemGrid) {
        loadItemList(itemGrid);
    }
});


// ========================================
// NEW ARRIVALS セクション（index.html）
// ========================================

async function loadNewArrivals(container) {
    try {
        const response = await fetch('../data/items.json');
        const data = await response.json();

        // 最新10件を表示
        const items = data.items.slice(0, 10);

        // 最終更新日時を表示
        const dateEl = document.getElementById('last-updated');
        if (dateEl && data.lastUpdated) {
            const d = new Date(data.lastUpdated);
            dateEl.textContent = `Last Updated: ${d.toLocaleDateString('ja-JP')}`;
        }

        container.innerHTML = items.map(item => createNewArrivalCard(item)).join('');

    } catch (error) {
        console.error('Failed to load items:', error);
        container.innerHTML = '<p class="text-center text-gray-400 col-span-full">アイテムの読み込みに失敗しました</p>';
    }
}

function createNewArrivalCard(item) {
    const tasteLabels = {
        'cyber': 'Cyberpunk', 'street': 'Street', 'wa-modern': 'Wa-Modern',
        'ryousangata': '量産型', 'jirai': '地雷系', 'fantasy': 'Fantasy',
        'casual': 'Casual', 'gothic': 'Gothic', 'pop': 'Pop'
    };
    const typeLabels = {
        'avatar': 'Avatar', 'costume': 'Costume', 'accessory': 'Accessory', 'texture': 'Texture'
    };

    const tasteTags = (item.taste || []).map(t =>
        `<span class="text-[9px] tracking-wider text-[#999] uppercase">#${tasteLabels[t] || t}</span>`
    ).join(' ');

    return `
        <a href="${item.boothUrl}" target="_blank" rel="noopener noreferrer"
           class="group block" data-item-id="${item.id}">
            <div class="aspect-[3/4] bg-[#E5E4DE] mb-3 overflow-hidden relative">
                <img src="${item.thumbnailUrl}" alt="${item.name}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                     onerror="this.style.display='none'">
                <div class="absolute top-2 right-2 bg-white/90 px-2 py-0.5 text-[9px] font-bold tracking-wider">
                    ${typeLabels[item.type] || item.type}
                </div>
            </div>
            <div class="space-y-1">
                <p class="text-[10px] text-[#999]">${item.shopName}</p>
                <h3 class="text-sm font-serif-display italic leading-snug line-clamp-2">${item.name}</h3>
                <div class="flex items-center justify-between">
                    <p class="text-xs font-bold">¥${item.price.toLocaleString()}</p>
                    <p class="text-[10px] text-[#999]">♡ ${item.likes}</p>
                </div>
                <div class="flex flex-wrap gap-1 mt-1">${tasteTags}</div>
            </div>
        </a>
    `;
}


// ========================================
// ITEM LIST ページ（list.html）
// ========================================

let allItems = [];
let currentCategory = 'all';
let currentTaste = null;
let currentType = null;
let searchQuery = '';

async function loadItemList(container) {
    try {
        const response = await fetch('../data/items.json');
        const data = await response.json();
        allItems = data.items;

        // 最終更新日時を表示
        const dateEl = document.getElementById('last-updated');
        if (dateEl && data.lastUpdated) {
            const d = new Date(data.lastUpdated);
            dateEl.textContent = `Last Updated: ${d.toLocaleDateString('ja-JP')}`;
        }

        // 件数表示
        updateCount();

        // 初回描画
        renderItems(container);

        // フィルター初期化
        initCategoryFilters(container);
        initTasteFilters(container);
        initTypeFilters(container);
        initSearchBar(container);

    } catch (error) {
        console.error('Failed to load items:', error);
        container.innerHTML = '<p class="text-center text-gray-400 col-span-full">アイテムの読み込みに失敗しました</p>';
    }
}

function getFilteredItems() {
    return allItems.filter(item => {
        const matchCategory = currentCategory === 'all' || item.category === currentCategory;
        const matchTaste = !currentTaste || (item.taste && item.taste.includes(currentTaste));
        const matchType = !currentType || item.type === currentType;
        const matchSearch = !searchQuery ||
            item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.shopName.toLowerCase().includes(searchQuery.toLowerCase());

        return matchCategory && matchTaste && matchType && matchSearch;
    });
}

function renderItems(container) {
    const filtered = getFilteredItems();
    updateCount(filtered.length);

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-16">
                <p class="text-lg text-[#999] mb-2">該当するアイテムがありません</p>
                <p class="text-xs text-[#BBB]">フィルターを変更してみてください</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => createItemCard(item)).join('');
}

function createItemCard(item) {
    const tasteLabels = {
        'cyber': 'Cyberpunk', 'street': 'Street', 'wa-modern': 'Wa-Modern',
        'ryousangata': '量産型', 'jirai': '地雷系', 'fantasy': 'Fantasy',
        'casual': 'Casual', 'gothic': 'Gothic', 'pop': 'Pop'
    };
    const typeLabels = {
        'avatar': 'Avatar', 'costume': 'Costume', 'accessory': 'Accessory', 'texture': 'Texture',
        'tool': 'Tool', 'pose': 'Pose'
    };

    const tasteTags = (item.taste || []).map(t =>
        `<span class="text-[9px] tracking-wider text-[#999] uppercase">#${tasteLabels[t] || t}</span>`
    ).join(' ');

    return `
        <div class="item-card group" data-item-id="${item.id}">
            <!-- Image -->
            <div class="aspect-[3/4] bg-[#E5E4DE] mb-4 overflow-hidden relative">
                <img src="${item.thumbnailUrl}" alt="${item.name}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                     onerror="this.style.display='none'">
                <div class="absolute top-2 right-2 bg-white/90 px-2 py-0.5 text-[9px] font-bold tracking-wider">
                    ${typeLabels[item.type] || item.type}
                </div>
            </div>

            <!-- Info -->
            <div class="space-y-1 mb-3">
                <p class="text-[10px] text-[#999]">${item.shopName}</p>
                <h3 class="text-sm font-serif-display italic leading-snug line-clamp-2">${item.name}</h3>
                <div class="flex items-center justify-between">
                    <p class="text-xs font-bold">¥${item.price.toLocaleString()}</p>
                    <p class="text-[10px] text-[#999]">♡ ${item.likes}</p>
                </div>
                <div class="flex flex-wrap gap-1">${tasteTags}</div>
            </div>

            <!-- Actions -->
            <div class="space-y-2">
                <a href="${item.boothUrl}" target="_blank" rel="noopener noreferrer"
                   class="block w-full border border-[#333] text-center py-2.5 text-xs tracking-widest font-bold
                          hover:bg-[#333] hover:text-white transition-colors">
                    BOOTHで見る →
                </a>
            </div>
        </div>
    `;
}

function updateCount(count) {
    const countEl = document.getElementById('item-count');
    if (countEl) {
        const total = count !== undefined ? count : allItems.length;
        countEl.textContent = `${total} items`;
    }
}


// ========================================
// フィルター初期化
// ========================================

function initCategoryFilters(container) {
    const btns = document.querySelectorAll('.filter-btn');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            btns.forEach(b => {
                b.classList.remove('bg-[#333333]', 'text-white');
                b.classList.add('hover:bg-gray-100');
            });
            btn.classList.remove('hover:bg-gray-100');
            btn.classList.add('bg-[#333333]', 'text-white');

            currentCategory = btn.getAttribute('data-filter');
            renderItems(container);
        });
    });
}

function initTasteFilters(container) {
    const btns = document.querySelectorAll('.taste-filter');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            const taste = btn.getAttribute('data-taste');
            if (currentTaste === taste) {
                currentTaste = null;
                btn.classList.remove('text-black', 'underline', 'font-bold');
            } else {
                currentTaste = taste;
                btns.forEach(b => b.classList.remove('text-black', 'underline', 'font-bold'));
                btn.classList.add('text-black', 'underline', 'font-bold');
            }
            renderItems(container);
        });
    });
}

function initTypeFilters(container) {
    const btns = document.querySelectorAll('.type-filter');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-type');
            if (currentType === type) {
                currentType = null;
                btn.classList.remove('text-black', 'underline', 'font-bold');
            } else {
                currentType = type;
                btns.forEach(b => b.classList.remove('text-black', 'underline', 'font-bold'));
                btn.classList.add('text-black', 'underline', 'font-bold');
            }
            renderItems(container);
        });
    });
}

function initSearchBar(container) {
    const searchInput = document.getElementById('item-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderItems(container);
        });
    }
}
