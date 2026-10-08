#target illustrator

// LIHC —— v1.9/v1.10 用 Illustrator 重拼六图 + 存 .ai 源文件 + 导出投稿 EPS
//
// 为什么要有这一步：.ai 与 EPS 必须来自**修好遮挡之后**的 SVG。旧组图源文件
// （23:39）与旧投稿格式（23:45）都是旧构图，已由 v19_archive_figs.py 搬进
// 历史版本_v1.0/第六轮_v1.9/。
//
// 输入：/tmp/aiwork/svg/Figure1..6.svg（面板已按 panel_A/panel_B/... 分组）
//       /tmp/aiwork/svg/FigureS1_calibration.svg
// 输出：/tmp/aiwork/ai/Figure1..6.ai、Figures_all_source.ai（6 画板总拼版）
//       /tmp/aiwork/eps/Figure1..6.eps、FigureS1_calibration.eps
// 全程 ASCII 路径（ExtendScript 对中文路径会解码出错）。
//
// ⚠️ 2026-10-05 定位到的真凶（害我们白查了两轮）：EPS 参数里
//    `o.overprint = PDFOverprint.PRESERVEPRINTOVERPRINT` 在 Illustrator 30.1.0
//    下抛 `Invalid enumeration value`，而它被下面的 try/catch 吞掉 → 表现为
//    "EPS 一个都没出、日志还写着 OK"。同理 `Compatibility.ILLUSTRATOR19` 也不存在。
//    可用的组合（实测）：compatibility=ILLUSTRATOR24 ＋ preview=COLORMACINTOSH
//    ＋ embedAllFonts/embedLinkedFiles ＋ cmykPostScript=false，**不要设 overprint**。
//
// 日志改成**增量写盘**：硬崩时也能看出停在哪一步（旧版把 log 攒到最后才写，
// 一次崩溃就把线索全丢了）。

var SRC = "/tmp/aiwork/svg/";
var AIO = "/tmp/aiwork/ai/";
var EPSO = "/tmp/aiwork/eps/";
var LOG = "/tmp/aiwork/log.txt";
var N = ["Figure1", "Figure2", "Figure3", "Figure4", "Figure5", "Figure6"];
var SUPP = "FigureS1_calibration";
var MM = 72.0 / 25.4;
var GAP = 20 * MM;

function ensure(p) { var f = new Folder(p); if (!f.exists) f.create(); }
ensure(AIO); ensure(EPSO);

function logline(s) {
    var f = new File(LOG);
    f.encoding = "UTF-8";
    f.open("a");
    f.writeln(s);
    f.close();
}

function aiOpt() {
    var o = new IllustratorSaveOptions();
    o.pdfCompatible = true;
    o.embedICCProfile = false;
    o.compressed = true;
    o.embedLinkedFiles = true;
    o.saveMultipleArtboards = false;
    return o;
}

// ⚠️ 不要设 o.overprint —— Illustrator 30.1.0 下该枚举非法（见文件头）。
function epsOpt() {
    var o = new EPSSaveOptions();
    o.preview = EPSPreview.COLORMACINTOSH;
    o.compatibility = Compatibility.ILLUSTRATOR24;
    o.embedAllFonts = true;
    o.embedLinkedFiles = true;
    o.cmykPostScript = false;
    o.saveMultipleArtboards = false;
    return o;
}

logline("START v=" + app.version);

// ---- 0) 先量尺寸与面板分组，量完即关，避免同时开 6 个文档 ----
var sizes = [];
for (var i = 0; i < N.length; i++) {
    try {
        var d = app.open(new File(SRC + N[i] + ".svg"));
        var a = d.artboards[0].artboardRect;
        var groups = [];
        for (var g = 0; g < d.groupItems.length; g++) {
            var nm = d.groupItems[g].name;
            if (nm && nm.length) groups.push(nm);
        }
        groups.sort();
        sizes.push([a[2] - a[0], a[1] - a[3]]);
        logline(N[i] + "\t" + (sizes[i][0] / MM).toFixed(1) + "x" +
                (sizes[i][1] / MM).toFixed(1) + " mm\tpanels=" + groups.join("+") +
                "\t图元=" + d.pageItems.length);
        d.close(SaveOptions.DONOTSAVECHANGES);
    } catch (e0) {
        logline(N[i] + "\tMEASURE FAIL: " + e0.message);
        try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e0b) { }
        sizes.push([0, 0]);
    }
}

// ---- 1) 逐张：打开 SVG -> 存 .ai -> 导出 EPS -> 关闭 ----
for (var k = 0; k < N.length; k++) {
    var doc = null;
    try {
        logline(N[k] + "\topen svg");
        doc = app.open(new File(SRC + N[k] + ".svg"));
        doc.saveAs(new File(AIO + N[k] + ".ai"), aiOpt());
        logline(N[k] + "\t.ai OK");
        doc.saveAs(new File(EPSO + N[k] + ".eps"), epsOpt());
        logline(N[k] + "\t.eps OK\t文字对象=" + doc.textFrames.length);
    } catch (e) {
        logline(N[k] + "\tFAIL: " + e.message);
    }
    try { if (doc) doc.close(SaveOptions.DONOTSAVECHANGES); } catch (e2) { }
}

// ---- 2) 补充图 S1：同样处理 ----
var dS = null;
try {
    dS = app.open(new File(SRC + SUPP + ".svg"));
    dS.saveAs(new File(AIO + SUPP + ".ai"), aiOpt());
    dS.saveAs(new File(EPSO + SUPP + ".eps"), epsOpt());
    logline(SUPP + "\t.ai + .eps OK");
} catch (e3) {
    logline(SUPP + "\tFAIL: " + e3.message);
}
try { if (dS) dS.close(SaveOptions.DONOTSAVECHANGES); } catch (e3b) { }

// ---- 3) 总拼版：新建文档 + 6 画板，逐张整组搬入 ----
//    ⚠️ artboards.add() 只对 app.documents.add() 新建的文档有效（历史踩坑）。
var master = null;
try {
    master = app.documents.add();
    var rects = [];
    var x = 0;
    for (var m = 0; m < N.length; m++) {
        var w = sizes[m][0], h = sizes[m][1];
        var r = [x, 0, x + w, -h];
        rects.push(r);
        if (m === 0) { master.artboards[0].artboardRect = r; master.artboards[0].name = N[m]; }
        else { master.artboards.add(r).name = N[m]; }
        x += w + GAP;
    }
    for (var p = 0; p < N.length; p++) {
        var sd = app.open(new File(SRC + N[p] + ".svg"));
        var grp = sd.groupItems.add();
        var items = [];
        for (var q = 0; q < sd.pageItems.length; q++) items.push(sd.pageItems[q]);
        for (var r2 = 0; r2 < items.length; r2++) items[r2].moveToBeginning(grp);
        grp.move(master, ElementPlacement.PLACEATBEGINNING);
        grp.position = new Point(rects[p][0], rects[p][1]);
        grp.name = N[p];
        grp.moveToBeginning(master.layers[0]);
        sd.close(SaveOptions.DONOTSAVECHANGES);
    }
    master.saveAs(new File(AIO + "Figures_all_source.ai"), aiOpt());
    logline("MASTER\t画板=" + master.artboards.length +
            "\t顶层组=" + master.groupItems.length);
} catch (e4) {
    logline("MASTER\tFAIL: " + e4.message);
}
try { if (master) master.close(SaveOptions.DONOTSAVECHANGES); } catch (e4b) { }

logline("DONE");
"DONE";
