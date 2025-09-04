// 全域 timer
let hintTimer = null;

window.showHint = function (msg, type = 'info', timeout = 2000) {
    const hint = document.getElementById('hint');
    if (!hint) return;

    hint.textContent = msg;

    // 移除舊的 type class
    hint.classList.remove('hint-error', 'hint-info');

    // 加上新的 type class
    hint.classList.add(`hint-${type}`);

    // 立即顯示
    hint.style.opacity = 1;

    // 如果前一次定時還沒結束，先清掉
    if (hintTimer) clearTimeout(hintTimer);

    // 設定新的消失計時
    hintTimer = setTimeout(() => {
        hint.style.opacity = 0;
        hint.className = '';
        hintTimer = null;
    }, timeout);
};

// 初始化 WebChannel
new QWebChannel(qt.webChannelTransport, function (channel) {
    const bridge = channel.objects.bridge;
    const hint = document.getElementById('hint');
    // 建立資料夾功能
    const btnNewFolder = document.getElementById('btnNewFolder');
    const btnReloadAll = document.getElementById('btnReloadAll');
    if (btnReloadAll) {
        btnReloadAll.addEventListener('click', function () {
            // 取得 img 目錄絕對路徑（由 Python 端判斷）
            bridge.openFolder('img');
        });
    }
    if (btnNewFolder) {
        btnNewFolder.addEventListener('click', function () {
            let folderName = prompt('請輸入新資料夾名稱：');
            if (!folderName) return;
            folderName = folderName.trim();
            // 禁止非法字元: \/:*?"<>|
            if (!folderName || /[\\/:*?"<>|]/.test(folderName)) {
                alert('資料夾名稱不能包含以下字元：\\ / : * ? " < > |，且不能為空白');
                return;
            }
            // 取得目前資料夾路徑，並去除每個路徑段的空白
            let curPath = '';
            const pathSpan = document.querySelector('.path');
            if (pathSpan) {
                curPath = pathSpan.textContent || '';
                // 將每個路徑段 trim
                curPath = curPath.split(/[/\\]/).map(s => s.trim()).filter(Boolean).join('\\');
            }
            bridge.createFolder(curPath, folderName);
        });
    }
    // 下載 Line 貼圖功能
    const btnDownloadLineSticker = document.getElementById('btnDownloadLineSticker');
    if (btnDownloadLineSticker) {
        btnDownloadLineSticker.addEventListener('click', function () {
            const url = prompt('請輸入 Line 貼圖網址：\n例如 https://store.line.me/stickershop/product/18301599/zh-Hant');
            if (!url) return;
            const curDir = getCurrentDir();
            bridge.downloadLineSticker(url, curDir);
        });
    }
    // 貼上圖片功能（由 PyQt 端處理剪貼簿）
    function getCurrentDir() {
        let curDir = '';
        const pathSpan = document.querySelector('.path');
        if (pathSpan) {
            curDir = pathSpan.getAttribute('data-curr-dir') || '';
        }
        return curDir;
    }
    // 按鈕貼上
    const btnPasteImage = document.getElementById('btnPasteImage');
    if (btnPasteImage) {
        btnPasteImage.addEventListener('click', function () {
            bridge.pasteImageFromClipboard(getCurrentDir());
        });
    }
    // Ctrl+V 支援
    document.addEventListener('paste', function (e) {
        bridge.pasteImageFromClipboard(getCurrentDir());
        e.preventDefault();
    });

    // 建立右鍵選單
    function createContextMenu(items, x, y) {
        // 先移除現有 context-menu
        document.querySelectorAll('.context-menu').forEach(menu => menu.remove());
        let menu = document.createElement('div');
        menu.className = 'context-menu';
        items.forEach(item => {
            let btn = document.createElement('div');
            btn.className = 'context-menu-item';
            btn.textContent = item.label;
            btn.onclick = function () {
                item.action();
                document.body.removeChild(menu);
            };
            menu.appendChild(btn);
        });
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        document.body.appendChild(menu);
        // 點擊其他地方關閉
        setTimeout(() => {
            document.addEventListener('click', function handler() {
                if (menu.parentNode) menu.parentNode.removeChild(menu);
                document.removeEventListener('click', handler);
            });
        }, 0);
    }

    document.querySelectorAll('.imgbox img').forEach(function (img) {
        img.addEventListener('click', function () {
            bridge.copyApngFile(img.getAttribute('data-path'));
            showHint('已複製檔案到剪貼簿');
        });
        // 支援拖曳圖片
        img.setAttribute('draggable', 'true');
        img.addEventListener('dragstart', function (e) {
            e.dataTransfer.setData('type', 'file');
            e.dataTransfer.setData('path', img.getAttribute('data-path'));
        });
        img.addEventListener('contextmenu', function (e) {
            e.preventDefault();
            const oldPath = img.getAttribute('data-path');
            const oldName = oldPath.split(/[/\\]/).pop();
            const dotIdx = oldName.lastIndexOf('.');
            const base = dotIdx > 0 ? oldName.slice(0, dotIdx) : oldName;
            const ext = dotIdx > 0 ? oldName.slice(dotIdx) : '';
            createContextMenu([{
                    label: '變更名稱',
                    action: function () {
                        const input = prompt('變更檔案名稱：', base);
                        if (input && input !== base) {
                            bridge.renameFile(oldPath, input + ext);
                        }
                    }
                },
                {
                    label: '刪除圖片',
                    action: function () {
                        if (confirm('確定要刪除圖片嗎？')) {
                            bridge.deleteFile(oldPath);
                        }
                    }
                }
            ], e.clientX, e.clientY);
        });
    });
    document.querySelectorAll('.folderbox').forEach(function (box) {
        box.addEventListener('dblclick', function () {
            // .. 或一般資料夾都要點兩下才切換
            bridge.openFolder(box.getAttribute('data-folder'));
        });
        // 支援拖曳資料夾（.. 不可被拖曳）
        if (!box.dataset.up) {
            box.setAttribute('draggable', 'true');
            box.addEventListener('dragstart', function (e) {
                e.dataTransfer.setData('type', 'folder');
                e.dataTransfer.setData('path', box.getAttribute('data-folder'));
            });
        }
        // 支援成為拖曳目標（.. 也可當目標）
        box.addEventListener('dragover', function (e) {
            e.preventDefault();
        });
        box.addEventListener('drop', function (e) {
            e.preventDefault();
            const srcType = e.dataTransfer.getData('type');
            const srcPath = e.dataTransfer.getData('path');
            const targetPath = box.getAttribute('data-folder');
            // .. 也可當目標（搬到上一層）
            if (srcType === 'file') {
                bridge.moveFile(srcPath, targetPath);
            } else if (srcType === 'folder') {
                if (srcPath !== targetPath && !targetPath.startsWith(srcPath + '\\')) {
                    bridge.moveFolder(srcPath, targetPath);
                }
            }
        });
        box.addEventListener('contextmenu', function (e) {
            // .. 資料夾不顯示右鍵選單
            if (box.dataset.up === '1') return;
            e.preventDefault();
            const oldPath = box.getAttribute('data-folder');
            const oldName = oldPath.split(/[/\\]/).pop();
            createContextMenu([{
                    label: '刪除資料夾',
                    action: function () {
                        if (confirm('確定要刪除此資料夾及其所有內容嗎？')) {
                            bridge.deleteFolder(oldPath);
                        }
                    }
                },
                {
                    label: '變更名稱',
                    action: function () {
                        const input = prompt('變更資料夾名稱：', oldName);
                        if (input && input !== oldName) {
                            bridge.renameFolder(oldPath, input);
                        }
                    }
                }
            ], e.clientX, e.clientY);
        });
    });
    // 點擊 breadcrumb 跳資料夾
    document.querySelectorAll('.breadcrumb').forEach(function (el) {
        el.addEventListener('click', function (e) {
            e.preventDefault();
            bridge.openFolder(el.getAttribute('data-folder'));
        });
    });

    // 搜尋功能
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');

    function filterImages() {
        const val = searchInput.value.trim().toLowerCase();
        document.querySelectorAll('.imgbox').forEach(function (box) {
            const img = box.querySelector('img');
            const name = img ? img.getAttribute('data-path').split(/[/\\]/).pop().toLowerCase() : '';
            if (!val || name.includes(val)) {
                box.style.display = '';
            } else {
                box.style.display = 'none';
            }
        });
    }
    if (searchInput) {
        searchInput.addEventListener('input', filterImages);
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                searchInput.value = '';
                filterImages();
            }
        });
    }
    if (clearSearch) {
        clearSearch.addEventListener('click', function () {
            searchInput.value = '';
            filterImages();
            searchInput.focus();
        });
    }

    // 設定視窗
    const modal = document.getElementById("configsMenu");
    const btnSettings = document.getElementById("btnSettings");
    const closeBtn = document.getElementById("closeSettings");

    // 打開設定視窗
    btnSettings.addEventListener("click", () => {
        modal.style.display = "block";
    });

    // 關閉設定視窗
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // 點背景也能關閉
    window.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });


    const themeSelect = document.getElementById("themeSelect");
    themeSelect.addEventListener("change", (e) => {
        const themeName = e.target.value;

        document.body.className = ""; // 清掉舊 class
        if (themeName) {
            document.body.classList.add(themeName);
        }
        bridge.saveConfig("theme", themeName);

    });
});