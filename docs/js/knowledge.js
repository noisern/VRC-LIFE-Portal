document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('knowledge-grid');
    const searchInput = document.getElementById('search-input');

    // Data embedded directly
    const allArticles = [
        {
            "id": "vol1",
            "number": "01",
            "title": "Vol.1 はじまりのガイド。必要なPC環境とインストールまでのステップ",
            "category": "VRChat入門",
            "image": "../images/knowledge_vol1_install.jpg",
            "summary": "スペックの確認、Steam/Metaアカウントの作成、VRChatアカウントの作り方など、最初の一歩をサポート。",
            "link": "vol1.html"
        },
        {
            "id": "vol2",
            "number": "02",
            "title": "Vol.2 新しい自分を動かす。各種設定とメニュー操作の基本",
            "category": "VRChat入門",
            "image": "../images/knowledge_vol2_settings.jpg",
            "summary": "移動方法、各種設定、メニュー画面の見方。「無言勢」という選択肢についても解説。",
            "link": "vol2.html"
        },
        {
            "id": "vol3",
            "number": "03",
            "title": "Vol.3 心地よい距離感と、出会いのエチケット",
            "category": "VRChat入門",
            "image": "../images/knowledge_vol3_etiquette.jpg",
            "summary": "インスタンスの違い、フレンド申請の送り方、日本人が集まる場所など、交流の基本とマナー。",
            "link": "vol3.html"
        },
        {
            "id": "vol4",
            "number": "04",
            "title": "Vol.4 自分という形を見つける。アバター展示ワールドとBoothの歩き方",
            "category": "VRChat入門",
            "image": "../images/knowledge_vol4_avatar.jpg",
            "summary": "パブリックアバターの着替え方、Boothという文化の紹介、アバター購入の第一歩。",
            "link": "vol4.html"
        },
        {
            "id": "vol5",
            "number": "05",
            "title": "Vol.5 世界を旅する。おすすめの初心者向けワールド・ガイド",
            "category": "VRChat入門",
            "image": "../images/knowledge_vol5_world.jpg",
            "summary": "ワールド検索のコツと、最初に行くべきおすすめの初心者向けワールド5選。",
            "link": "vol5.html"
        },
        {
            "id": "2",
            "number": "06",
            "title": "Unity 2022への移行とアバターアップロードの基本",
            "category": "改変基礎",
            "image": "../images/fashion.jpg",
            "summary": "最新のUnity 2022環境への移行手順と、VCCを使用したアバターのアップロード方法をステップバイステップで紹介。",
            "link": "article_02.html"
        },
        {
            "id": "3",
            "number": "07",
            "title": "解決！アバターがピンク色（Shaderエラー）になった時の対処法",
            "category": "トラブル解決",
            "image": "../images/trend.jpg",
            "summary": "ワールドやアバターがピンク色になってしまう「ショッキングピンク」現象。その原因と、シェーダー設定による解決策を解説。",
            "link": "article_03.html"
        }
    ];

    // Initial Render
    renderArticles(allArticles);

    // Render articles function
    function renderArticles(articles) {
        grid.innerHTML = '';

        if (articles.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center py-20 text-[#999999]">No articles found matching your criteria.</div>';
            return;
        }

        articles.forEach(article => {
            const card = document.createElement('a');
            card.href = article.link;
            card.className = 'group block bg-white border border-[#E5E4DE] overflow-hidden hover:border-[#999999] hover:shadow-lg transition-all duration-300 relative';

            // Category Badge Color (Adjusted for Light Theme)
            let categoryClass = 'bg-[#F0F0F0] text-[#666666]';
            if (article.category === 'VRChat入門') categoryClass = 'bg-blue-50 text-blue-600 border border-blue-100';
            if (article.category === '改変基礎') categoryClass = 'bg-green-50 text-green-600 border border-green-100';
            if (article.category === 'トラブル解決') categoryClass = 'bg-red-50 text-red-600 border border-red-100';

            card.innerHTML = `
                <div class="aspect-[16/9] overflow-hidden relative">
                    <img src="${article.image}" alt="${article.title}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105">
                    
                    <!-- Number Overlay (Only for VRChat入門) -->
                    ${article.category === 'VRChat入門' ? `
                    <div class="absolute top-0 right-2 text-7xl font-thin text-white/40 select-none z-10 transition-colors group-hover:text-white/60">
                        ${article.number}
                    </div>
                    ` : ''}
                </div>
                <div class="p-6 relative z-20">
                    <div class="mb-4">
                        <span class="text-[10px] uppercase tracking-widest px-2 py-1 rounded-sm ${categoryClass}">
                            ${article.category}
                        </span>
                    </div>
                    <h3 class="text-xl font-light text-[#333333] mb-3 group-hover:text-black transition-colors leading-relaxed tracking-wide">${article.title}</h3>
                    <p class="text-sm text-[#666666] line-clamp-2 leading-relaxed font-light">${article.summary}</p>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Filter Logic for Banners
    let currentCategory = 'all';
    const banners = document.querySelectorAll('.category-banner');
    banners.forEach(banner => {
        banner.addEventListener('click', () => {
            currentCategory = banner.getAttribute('data-category');

            // Filter articles
            filterArticles(currentCategory, searchInput.value);

            // Smooth scroll to grid
            grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // Search Logic
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        filterArticles(currentCategory, query);
    });

    function filterArticles(category, query) {
        const lowerQuery = query.toLowerCase();

        const filtered = allArticles.filter(article => {
            const matchesCategory = category === 'all' || article.category === category;
            const matchesSearch = article.title.toLowerCase().includes(lowerQuery) ||
                article.summary.toLowerCase().includes(lowerQuery);
            return matchesCategory && matchesSearch;
        });

        renderArticles(filtered);
    }
});
