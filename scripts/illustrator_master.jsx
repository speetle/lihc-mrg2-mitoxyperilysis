#target illustrator

// 总拼版 v3：新建 6 画板文档 → 逐张打开 SVG、把全部图元收进一个组 → 整组搬入对应画板
var SRC = "/tmp/aiwork/";
var OUT = "/tmp/aiwork/ai/";
var N = ["Figure1", "Figure2", "Figure3", "Figure4", "Figure5", "Figure6"];
var MM = 72.0 / 25.4;
var GAP = 20 * MM;
var log = [];

// 1) 量尺寸
var sizes = [];
for (var i = 0; i < N.length; i++) {
    var d0 = app.open(new File(SRC + N[i] + ".svg"));
    var a0 = d0.artboards[0].artboardRect;
    sizes.push([a0[2] - a0[0], a0[1] - a0[3]]);
    d0.close(SaveOptions.DONOTSAVECHANGES);
}

// 2) 新建文档 + 6 画板（add(rect) 只在新建文档里可用）
var doc = app.documents.add();
var rects = [];
var x = 0;
for (var k = 0; k < N.length; k++) {
    var w = sizes[k][0], h = sizes[k][1];
    var r = [x, 0, x + w, -h];
    rects.push(r);
    if (k === 0) { doc.artboards[0].artboardRect = r; doc.artboards[0].name = N[k]; }
    else { doc.artboards.add(r).name = N[k]; }
    x += w + GAP;
}
log.push("画板数=" + doc.artboards.length);

// 3) 逐张搬入
for (var p = 0; p < N.length; p++) {
    try {
        var d = app.open(new File(SRC + N[p] + ".svg"));
        var g = d.groupItems.add();
        var items = [];
        for (var q = 0; q < d.pageItems.length; q++) items.push(d.pageItems[q]);
        for (var r2 = 0; r2 < items.length; r2++) items[r2].moveToBeginning(g);
        g.move(doc, ElementPlacement.PLACEATBEGINNING);
        g.position = new Point(rects[p][0], rects[p][1]);
        g.name = N[p];
        g.moveToBeginning(doc.layers[0]);          // 让每组直接挂在图层下，便于在图层面板里点选
        log.push(N[p] + " OK  组内图元=" + g.pageItems.length + "  组尺寸=" +
                 g.width.toFixed(1) + "x" + g.height.toFixed(1) + "pt");
        d.close(SaveOptions.DONOTSAVECHANGES);
    } catch (e) {
        log.push(N[p] + " FAIL: " + e.message);
        try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e2) {}
    }
}

// 4) 存盘（saveMultipleArtboards=false → 只出一个 .ai，内含 6 画板）
try {
    var opt = new IllustratorSaveOptions();
    opt.pdfCompatible = true;
    opt.saveMultipleArtboards = false;
    opt.embedLinkedFiles = true;
    opt.compressed = true;
    doc.saveAs(new File(OUT + "Figures_all_source.ai"), opt);
    log.push("已存 Figures_all_source.ai  画板=" + doc.artboards.length + " 顶层组=" + doc.groupItems.length);
} catch (e3) {
    log.push("SAVE FAIL: " + e3.message);
}
doc.close(SaveOptions.DONOTSAVECHANGES);
log.join("\n");
