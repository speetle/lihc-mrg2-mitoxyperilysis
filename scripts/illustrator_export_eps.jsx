#target illustrator

// 导出投稿用 EPS —— 用与本机首次成功完全一致的一组选项（preview 走默认 COLORMACINTOSH）
// 逐张处理并即时落盘，避免一次性任务过重被 AppleEvent 掐断。
var SRC = "/tmp/aiexp/ai/";
var SVG = "/tmp/aiexp/svg/";
var OUT = "/tmp/aiexp/eps2/";
var AIOUT = "/tmp/aiexp/ai2/";
var log = [];

function ensure(p) { var f = new Folder(p); if (!f.exists) f.create(); }
ensure(OUT); ensure(AIOUT);

function epsOpt() {
    var o = new EPSSaveOptions();
    o.preview = EPSPreview.COLORMACINTOSH;
    o.compatibility = Compatibility.ILLUSTRATOR24;
    o.embedAllFonts = true;
    o.embedLinkedFiles = true;
    o.cmykPostScript = false;
    o.overprint = PDFOverprint.PRESERVEPRINTOVERPRINT;
    o.saveMultipleArtboards = false;
    return o;
}

function doOne(srcPath, outName) {
    var doc = app.open(new File(srcPath));
    doc.saveAs(new File(OUT + outName + ".eps"), epsOpt());
    doc.close(SaveOptions.DONOTSAVECHANGES);
    log.push(outName + ".eps OK");
}

var N = ["Figure1", "Figure2", "Figure3", "Figure4", "Figure5", "Figure6"];
for (var i = 0; i < N.length; i++) {
    try { doOne(SRC + N[i] + ".ai", N[i]); }
    catch (e) { log.push(N[i] + " FAIL: " + e.message); }
}

try {
    var d = app.open(new File(SVG + "FigureS1_calibration.svg"));
    d.saveAs(new File(AIOUT + "FigureS1_calibration.ai"), new IllustratorSaveOptions());
    d.saveAs(new File(OUT + "FigureS1_calibration.eps"), epsOpt());
    d.close(SaveOptions.DONOTSAVECHANGES);
    log.push("FigureS1_calibration.eps OK");
} catch (e3) { log.push("FigureS1 FAIL: " + e3.message); }

log.join("\n");
