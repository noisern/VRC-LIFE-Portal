// world.js
// Handles fetching, filtering, and rendering of World items.

console.log("Loading World Script...");

let allWorlds = [];
let currentCategory = 'ALL';
let currentSort = 'newest'; // 'newest', 'oldest'

// DOM Elements
const grid = document.getElementById('worlds-grid');
const filterContainer = document.getElementById('filter-container'); // Tabs

async function init() {
    try {
        const response = await fetch('../data/worlds.json');
        if (!response.ok) throw new Error('Failed to fetch worlds data');

        allWorlds = await response.json();
        console.log(`Loaded ${allWorlds.length} worlds.`);

        // Initial Render
        renderWorlds();

        // Init Filters
        initCategoryFilters();

    } catch (error) {
        console.error(error);
        if (grid) {
            grid.innerHTML = `<div class="col-span-full text-center py-20 text-red-500">Failed to load data.</div>`;
        }
    }
}

function initCategoryFilters() {
    if (!filterContainer) return;

    const bitns = filterContainer.querySelectorAll('.filter-btn');
    bitns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            bitns.forEach(b => b.classList.remove('active', 'bg-black', 'text-white'));
            bitns.forEach(b => b.classList.add('bg-white', 'text-gray-600'));

            btn.classList.remove('bg-white', 'text-gray-600');
            btn.classList.add('active', 'bg-black', 'text-white');

            // Set category
            currentCategory = btn.getAttribute('data-tag');
            renderWorlds();
        });
    });
}

function getFilteredWorlds() {
    let filtered = allWorlds;

    // 1. Filter by Category
    if (currentCategory && currentCategory !== 'ALL') {
        filtered = filtered.filter(w => {
            // Case insensitive match
            return w.category && w.category.toUpperCase() === currentCategory.toUpperCase();
        });
    }

    // 2. Sort
    filtered.sort((a, b) => {
        const dateA = new Date(a.date || a.fetchedAt);
        const dateB = new Date(b.date || b.fetchedAt);

        if (currentSort === 'newest') {
            return dateB - dateA;
        } else {
            return dateA - dateB;
        }
    });

    return filtered;
}

function renderWorlds() {
    if (!grid) return;
    grid.innerHTML = '';

    const worlds = getFilteredWorlds();

    if (worlds.length === 0) {
        grid.innerHTML = `<div class="col-span-full text-center py-20 text-gray-400">No worlds found.</div>`;
        return;
    }

    worlds.forEach(world => {
        const card = createWorldCard(world);
        grid.appendChild(card);
    });
}

function createWorldCard(world) {
    // Layout: Monotone / Magazine Style
    // Image aspect ratio? 3:4 or 16:9? VRChat worlds are usually 16:9 thumbnails.
    // User requested "Monotone / Magazine style".

    const div = document.createElement('div');
    div.className = 'group flex flex-col bg-white border border-transparent hover:border-black transition-all duration-300';

    // Image Container
    const imgContainer = document.createElement('a');
    imgContainer.href = world.url;
    imgContainer.target = "_blank";
    imgContainer.rel = "noopener noreferrer";
    // Aspect ratio 16:9 for worlds usually looks best
    imgContainer.className = 'relative aspect-video w-full overflow-hidden bg-gray-100';

    const img = document.createElement('img');
    img.src = world.thumbnailUrl || '../images/logo.png'; // Fallback
    img.alt = world.name;
    img.className = 'w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 filter grayscale group-hover:grayscale-0';

    imgContainer.appendChild(img);

    // Content Container
    const content = document.createElement('div');
    content.className = 'p-4 flex flex-col flex-1';

    // Category Tag (Small, Top)
    const meta = document.createElement('div');
    meta.className = 'flex justify-between items-center mb-2';

    const catSpan = document.createElement('span');
    catSpan.className = 'text-[10px] uppercase tracking-widest text-gray-400 border border-gray-200 px-2 py-0.5';
    catSpan.textContent = world.category || 'OTHER';

    const dateSpan = document.createElement('span');
    dateSpan.className = 'text-[10px] text-gray-400 tracking-wider font-light';
    // Format date YYYY.MM.DD
    try {
        const d = new Date(world.date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        dateSpan.textContent = `${year}.${month}.${day}`;
    } catch (e) {
        dateSpan.textContent = '';
    }

    meta.appendChild(catSpan);
    meta.appendChild(dateSpan);

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-serif-display italic font-bold leading-tight mb-1 group-hover:underline decoration-1 underline-offset-4';
    title.style.fontFamily = "'Shippori Mincho', serif"; // Force Serif for Japanese
    title.textContent = world.name;

    // Author
    const author = document.createElement('p');
    author.className = 'text-xs text-gray-500 mb-3 font-light';
    if (world.authorUrl) {
        author.innerHTML = `by <a href="${world.authorUrl}" target="_blank" class="hover:text-black hover:underline transition-colors">${world.author || 'Unknown'}</a>`;
    } else {
        author.textContent = `by ${world.author || 'Unknown'}`;
    }

    // Description
    const desc = document.createElement('p');
    desc.className = 'text-xs text-gray-600 leading-relaxed line-clamp-3 font-light';
    desc.textContent = world.description || '';

    content.appendChild(meta);
    content.appendChild(title);
    content.appendChild(author);
    content.appendChild(desc);

    div.appendChild(imgContainer);
    div.appendChild(content);

    return div;
}

// Start
document.addEventListener('DOMContentLoaded', init);
