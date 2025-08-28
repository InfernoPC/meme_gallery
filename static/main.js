// 初始化 WebChannel
new QWebChannel(qt.webChannelTransport, function (channel) {
    const bridge = channel.objects.bridge;
    const hint = document.getElementById('hint');
    document.querySelectorAll('.imgbox img').forEach(function (img) {
        img.addEventListener('click', function () {
            bridge.copyApngFile(img.getAttribute('data-path'));
            hint.textContent = '已複製檔案到剪貼簿';
            hint.style.opacity = 1;
            setTimeout(() => hint.style.opacity = 0, 900);
        });
        img.addEventListener('dragstart', e => e.preventDefault());
    });
    document.querySelectorAll('.folderbox').forEach(function (box) {
        box.addEventListener('click', function () {
            bridge.openFolder(box.getAttribute('data-folder'));
        });
    });
    document.getElementById('backbtn').addEventListener('click', function () {
        bridge.goBack();
    });
});