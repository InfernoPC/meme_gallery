    // 初始化 WebChannel
    new QWebChannel(qt.webChannelTransport, function (channel) {
        const bridge = channel.objects.bridge;
        const hint = document.getElementById('hint');

        // 建立資料夾功能
        const btnNewFolder = document.getElementById('btnNewFolder');
        if (btnNewFolder) {
            btnNewFolder.addEventListener('click', function() {
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
    // 建立右鍵選單
    function createContextMenu(items, x, y) {
        let menu = document.createElement('div');
        menu.className = 'context-menu';
        items.forEach(item => {
            let btn = document.createElement('div');
            btn.className = 'context-menu-item';
            btn.textContent = item.label;
            btn.onclick = function() {
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
            hint.textContent = '已複製檔案到剪貼簿';
            hint.style.opacity = 1;
            setTimeout(() => hint.style.opacity = 0, 900);
        });
        // 支援拖曳圖片
        img.setAttribute('draggable', 'true');
        img.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('type', 'file');
            e.dataTransfer.setData('path', img.getAttribute('data-path'));
        });
        img.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            const oldPath = img.getAttribute('data-path');
            const oldName = oldPath.split(/[/\\]/).pop();
            const dotIdx = oldName.lastIndexOf('.');
            const base = dotIdx > 0 ? oldName.slice(0, dotIdx) : oldName;
            const ext = dotIdx > 0 ? oldName.slice(dotIdx) : '';
            createContextMenu([
                {
                    label: '刪除圖片',
                    action: function() {
                        if (confirm('確定要刪除圖片嗎？')) {
                            bridge.deleteFile(oldPath);
                        }
                    }
                },
                {
                    label: '變更名稱',
                    action: function() {
                        const input = prompt('變更檔案名稱：', base);
                        if (input && input !== base) {
                            bridge.renameFile(oldPath, input + ext);
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
            box.addEventListener('dragstart', function(e) {
                e.dataTransfer.setData('type', 'folder');
                e.dataTransfer.setData('path', box.getAttribute('data-folder'));
            });
        }
        // 支援成為拖曳目標（.. 也可當目標）
        box.addEventListener('dragover', function(e) {
            e.preventDefault();
        });
        box.addEventListener('drop', function(e) {
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
        box.addEventListener('contextmenu', function(e) {
            // .. 資料夾不顯示右鍵選單
            if (box.dataset.up === '1') return;
            e.preventDefault();
            const oldPath = box.getAttribute('data-folder');
            const oldName = oldPath.split(/[/\\]/).pop();
            createContextMenu([
                {
                    label: '刪除資料夾',
                    action: function() {
                        if (confirm('確定要刪除此資料夾及其所有內容嗎？')) {
                            bridge.deleteFolder(oldPath);
                        }
                    }
                },
                {
                    label: '變更名稱',
                    action: function() {
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
        document.querySelectorAll('.imgbox').forEach(function(box) {
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
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                searchInput.value = '';
                filterImages();
            }
        });
    }
    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            searchInput.value = '';
            filterImages();
            searchInput.focus();
        });
    }
});