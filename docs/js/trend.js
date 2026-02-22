/* Trend Page Logic */
document.addEventListener('DOMContentLoaded', () => {
    fetch('../data/trends.json')
        .then(response => {
            if (!response.ok) throw new Error("Trends not found");
            return response.json();
        })
        .then(data => {
            renderTrends(data);
        })
        .catch(err => {
            console.error("Error loading trends:", err);
            document.getElementById('trend-list').innerHTML =
                `<p class="text-center text-gray-500 py-10">最新のトレンドを読み込めませんでした。</p>`;
        });
});

function renderTrends(items) {
    const listContainer = document.getElementById('trend-list');
    listContainer.innerHTML = '';

    if (items.length === 0) {
        listContainer.innerHTML = `<p class="text-center text-gray-500 py-10">まだ記事がありません。</p>`;
        return;
    }

    items.forEach(item => {
        // Create Card Element
        const card = document.createElement('article');
        card.className = "group border-b border-gray-200 dark:border-gray-800 py-8 first:pt-0 last:border-0 transition-colors hover:bg-gray-50 dark:hover:bg-gray-900/50 -mx-4 px-4 rounded-xl";

        // Tags Logic
        const tagsHtml = item.tags
            ? item.tags.map(tag => `<span class="text-xs font-medium tracking-wider text-gray-500 uppercase mr-2">#${tag.replace('#', '')}</span>`).join('')
            : '';

        // Safely insert HTML
        card.innerHTML = `
            <div class="flex flex-col md:flex-row gap-4 md:items-start">
                <div class="md:w-32 flex-shrink-0">
                    <time class="text-sm text-gray-400 font-mono">${item.date || 'Today'}</time>
                </div>
                <div class="flex-1 space-y-3">
                    <div class="flex flex-wrap gap-2 items-center">
                        ${tagsHtml}
                    </div>
                    <h2 class="text-xl md:text-2xl font-light leading-tight group-hover:text-gray-600 transition-colors">
                        <a href="${item.sourceUrl}" target="_blank" rel="noopener" class="block">
                            ${item.title}
                        </a>
                    </h2>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed line-clamp-3">
                        ${item.content}
                    </p>
                    <div class="pt-2">
                        <a href="${item.sourceUrl}" target="_blank" rel="noopener" class="inline-flex items-center text-xs text-gray-400 hover:text-black dark:hover:text-white transition-colors uppercase tracking-widest">
                            Read Source <span class="ml-1">→</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
        listContainer.appendChild(card);
    });
}
