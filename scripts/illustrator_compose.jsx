#target illustrator

// 学生3 LIHC —— 用 Illustrator 组图并保存 .ai 源文件
// 输入：/tmp/aiwork/FigureN.svg（面板已按 panel_A/panel_B/... 分组）
// 输出：/tmp/aiwork/ai/FigureN.ai  以及  /tmp/aiwork/ai/Figures_全部_源文件.ai（6 画板）
// 全程 ASCII 路径，避免 ExtendScript 中文路径解码问题。

var SRC = "/tmp/aiwork/";
var OUT = "/tmp/aiwork/ai/";
var NAMES = ["Figure1", "Figure2", "Figure3", "Figure4", "Figure5", "Figure6"];
var MM = 72.0 / 25.4;          // 1 mm = 2.8346 pt
var WIDTH_MM = 183.0;          // 双栏印刷宽

function ensure(folder) {
    var f = new Folder(folder);
    if (!f.exists) f.create();
    return f;
}

function openSvg(path) {
    var f = new File(path);
    if (!f.exists) return null;
    return app.open(f);
}

function panelNames(doc) {
    var out = [];
    for (var i = 0; i < doc.groupItems.length; i++) {
        var nm = doc.groupItems[i].name;
        if (nm && nm.length) out.push(nm);
    }
    out.sort();
    return out;
}

function saveAi(doc, path) {
    var opt = new IllustratorSaveOptions();
    opt.pdfCompatible = true;
    opt.embedICCProfile = false;
    opt.compressed = true;
    opt.embedLinkedFiles = true;
    doc.saveAs(new File(path), opt);
}

ensure(OUT);

var log = [];
var master = null;
var masterAb = null;

for (var i = 0; i < NAMES.length; i++) {
    var n = NAMES[i];
    var doc = openSvg(SRC + n + ".svg");
    if (doc === null) { log.push(n + "\tMISSING"); continue; }

    var ab = doc.artboards[0].artboardRect;      // [l, t, r, b]
    var wpt = ab[2] - ab[0];
    var hpt = ab[1] - ab[3];
    var panels = panelNames(doc);

    // 导出时先按 183 mm 宽度等比归一（SVG 已是该宽，此处只做记录与校正）
    if (Math.abs(wpt / MM - WIDTH_MM) > 2.0) {
        log.push(n + "\tWARN 宽度 " + (wpt / MM).toFixed(1) + " mm != " + WIDTH_MM + " mm，未缩放");
    }

    saveAi(doc, OUT + n + ".ai");
    log.push(n + "\tpanels=" + panels.join("+") +
             "\t尺寸=" + (wpt / MM).toFixed(1) + "x" + (hpt / MM).toFixed(1) + " mm" +
             "\t图元=" + doc.pageItems.length);
    doc.close(SaveOptions.DONOTSAVECHANGES);
}

// ---- 总拼版：新建文档，每个 Figure 一个画板 ----
try {
    var sizes = [];
    for (var k = 0; k < NAMES.length; k++) {
        var d = openSvg(SRC + NAMES[k] + ".svg");
        if (d === null) { sizes.push(null); continue; }
        var a = d.artboards[0].artboardRect;
        sizes.push([a[2] - a[0], a[1] - a[3]]);
        d.close(SaveOptions.DONOTSAVECHANGES);
    }
    master = app.documents.add();
    master.artboards[0].artboardRect = [0, 0, sizes[0][0], -sizes[0][1]];
    master.artboards[0].name = "Figure 1";
    for (var m = 1; m < NAMES.length; m++) {
        var idx = master.artboards.add([0, 0, sizes[m][0], -sizes[m][1]]);
        idx.name = "Figure " + (m + 1);
    }
    for (var p = 0; p < NAMES.length; p++) {
        var srcDoc = openSvg(SRC + NAMES[p] + ".svg");
        var a2 = srcDoc.artboards[0].artboardRect;
        var bb = [0, 0, a2[2] - a2[0], -(a2[1] - a2[3])];
        var group = srcDoc.groupItems.add();
        group.name = NAMES[p];
        var items = [];
        for (var q = 0; q < srcDoc.pageItems.length; q++) items.push(srcDoc.pageItems[q]);
        for (var r = 0; r < items.length; r++) items[r].moveToBeginning(group);
        var target = master.artboards[p].artboardRect;
        group.move(master, ElementPlacement.PLACEATBEGINNING);
        group.position = new Point(target[0], target[1]);
        srcDoc.close(SaveOptions.DONOTSAVECHANGES);
    }
    saveAi(master, OUT + "Figures_all_source.ai");
    log.push("MASTER\t画板=" + master.artboards.length + "\t图元=" + master.pageItems.length);
    master.close(SaveOptions.DONOTSAVECHANGES);
} catch (e) {
    log.push("MASTER\tFAILED " + e.message);
}

var summary = log.join("\n");
summary;
