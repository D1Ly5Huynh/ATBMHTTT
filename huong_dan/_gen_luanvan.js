"use strict";
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents,
  LevelFormat, NumberFormat, Math: OmmlMath, MathRun, MathFraction, MathDenominator,
  MathNumerator,
} = require("/tmp/docx-build/node_modules/docx");

const FONT = "Times New Roman";
const BODY = 26; // 13pt
const SMALL = 20; // 10pt
const TW = 9071; // A4, left 3cm, right 2cm
const LINE = 360; // 1.5
const NAVY = "1F4E79";
const GRAY = "F2F2F2";
const WHITE = "FFFFFF";
const GREEN = "E2EFDA";
const RED = "FCE4D6";

const thin = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: thin, bottom: thin, left: thin, right: thin };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function runs(text, extra = {}) {
  const size = extra.size || BODY;
  const font = extra.font || FONT;
  const color = extra.color;
  const italics = extra.italics || false;
  const parts = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) {
      parts.push(new TextRun({ text: text.slice(last, m.index), font, size, italics, color, bold: extra.bold }));
    }
    if (m[0].startsWith("**")) {
      parts.push(new TextRun({ text: m[0].slice(2, -2), font, size, bold: true, italics, color }));
    } else {
      parts.push(new TextRun({ text: m[0].slice(1, -1), font: "Courier New", size: Math.max(size - 2, 18), italics, color }));
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    parts.push(new TextRun({ text: text.slice(last), font, size, italics, color, bold: extra.bold }));
  }
  if (!parts.length) parts.push(new TextRun({ text: text || "", font, size, italics, color, bold: extra.bold }));
  return parts;
}

function p(text, extra = {}) {
  return new Paragraph({
    alignment: extra.align || AlignmentType.JUSTIFIED,
    spacing: { after: extra.after ?? 160, before: extra.before ?? 0, line: extra.line ?? LINE },
    numbering: extra.num,
    indent: extra.indent,
    border: extra.border,
    children: extra.children || runs(text, extra),
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: NAVY })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, font: FONT, size: 28, bold: true, color: NAVY })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, font: FONT, size: 26, bold: true, italics: true })],
  });
}

function cap(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 20, italics: true })],
  });
}

function cell(text, width, opts = {}) {
  const fill = opts.fill || WHITE;
  const color = opts.color;
  const bold = !!opts.bold || !!opts.header;
  const size = opts.size || (opts.header ? SMALL : SMALL);
  const align = opts.align || (opts.header ? AlignmentType.CENTER : AlignmentType.LEFT);
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill, type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [
      new Paragraph({
        alignment: align,
        spacing: { after: 0, line: 276 },
        children: runs(String(text), { size, bold, color, italics: opts.italics }),
      }),
    ],
  });
}

function table(colWidths, header, rows, opts = {}) {
  const sum = colWidths.reduce((a, b) => a + b, 0);
  if (sum !== TW) throw new Error(`colWidths ${sum} != ${TW}`);
  const headerFill = opts.headerFill || NAVY;
  const headerColor = opts.headerColor || WHITE;
  const stripe = opts.stripe !== false;
  const body = [
    new TableRow({
      tableHeader: true,
      children: header.map((h, i) =>
        cell(h, colWidths[i], { header: true, fill: headerFill, color: headerColor, align: AlignmentType.CENTER })
      ),
    }),
  ];
  rows.forEach((r, ri) => {
    const fill = stripe && ri % 2 === 1 ? GRAY : WHITE;
    body.push(
      new TableRow({
        children: r.map((c, i) =>
          cell(c, colWidths[i], {
            fill,
            size: opts.size || SMALL,
            align: opts.aligns ? opts.aligns[i] : AlignmentType.LEFT,
            bold: opts.boldCol && opts.boldCol.has(i),
          })
        ),
      })
    );
  });
  return new Table({
    width: { size: TW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: body,
  });
}

function mathPara(children) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 160 },
    children: [new OmmlMath({ children })],
  });
}

const children = [];

// ===== COVER =====
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text: "HỌC PHẦN AN TOÀN BẢO MẬT HỆ THỐNG THÔNG TIN", font: FONT, size: 24, bold: true, color: NAVY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [new TextRun({ text: "(ATBMHTTT)", font: FONT, size: 22, color: NAVY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 600, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 1 } },
    children: [new TextRun({ text: "LUẬN VĂN", font: FONT, size: 40, bold: true, color: NAVY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 80, line: 360 },
    children: [new TextRun({ text: "Đánh giá và mở rộng tấn công đối kháng XSS", font: FONT, size: 32, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80, line: 360 },
    children: [new TextRun({ text: "dựa trên học tăng cường sâu", font: FONT, size: 32, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400, line: 360 },
    children: [new TextRun({ text: "theo khung Pasini et al. (JSS 2026)", font: FONT, size: 28, italics: true })],
  }),
  p("Chen et al. (2022) báo Escape Rate ~99% mà không kiểm tra payload còn là XSS. Pasini et al. (2026) thêm Oracle DOM và chỉ ra preprocess/OOV. Luận văn bám khung Oracle → Ruin Rate → Oracle-in-the-loop, siết Oracle thành thực thi JavaScript, và đo thêm CRS/DOMPurify bằng TASR.", { after: 400 }),
  p("**Bài gốc:** Pasini, Maragliano, Kim, Tonella. Cross-site scripting adversarial attacks based on deep reinforcement learning: Evaluation and extension study. Journal of Systems and Software, 2026. arXiv:2502.19095v2. Artifact GitHub `GianlucaMaragliano/Adversarial_RL_XSS` commit `a299bb6`."),
  p("**Phạm vi:** localhost; dataset Mereani / artifact `data/10`; CRS 4 lab. Không WAF cloud, không LLM generator. Bám PDF v2 (RQ1–RQ3), không dùng đánh số RQ1–RQ4 của bản HTML cũ."),
  new Paragraph({ spacing: { before: 600, after: 80 }, children: [new TextRun({ text: "Họ và tên: ________________________________", font: FONT, size: BODY })] }),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "MSSV: ____________________________________", font: FONT, size: BODY })] }),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Giảng viên hướng dẫn: ______________________", font: FONT, size: BODY })] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 600 },
    children: [new TextRun({ text: "Tháng 9 năm 2026", font: FONT, size: 24 })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===== TÓM TẮT + TOC =====
children.push(
  h1("Tóm tắt"),
  p("Luận văn tái lập và đánh giá lại công trình Pasini et al. (JSS 2026) về tấn công đối kháng XSS bằng PPO. Trên đúng artifact và split `data/10` (nhánh A), detector MLP/LSTM/CNN trùng Table 4 (Precision 99,67%, Recall 100%, Accuracy/F1 99,83%). PPO không Oracle đạt Escape Rate ~99% (LSTM 98,78%); khi nhét Oracle DOM vào reward, RQ3 vẫn ER > 96% (LSTM 98,34%, MLP 97,89%, CNN 96,00%, cả ba 250k bước). Thủ phạm là token-id không ổn định và OOV `None` (TH2), không phải “RL sinh XSS mạnh”."),
  p("Khi khép encode và đổi Oracle thành thực thi JavaScript (nhánh B), cùng 27 action Table 2, PPO ER trung bình 0,75%; Oracle-in-loop kéo PPO về sàn false-negative 0,25% (Dueling DQN 1,08%), RR = 0. Trên lab CRS paranoia 1, catalog Chen/Pasini và agent LSTM có TASR = 0. DOMPurify: HTTP lọt nhưng hết độc (Δ = 1). Không train RL trên CRS vì chưa có primitive BYPASS_EXEC."),
  p("**Từ khóa:** XSS, tấn công đối kháng, PPO, Oracle thực thi, Ruin Rate, TASR, OWASP CRS, DOMPurify."),
  h1("Mục lục"),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===== CHƯƠNG 1 =====
children.push(
  h1("Chương 1. Mở đầu"),
  h2("1.1. Bối cảnh"),
  p("Cross-site scripting (XSS) chèn mã vào trang web để trình duyệt nạn nhân thực thi. Detector học sâu (Fang et al. 2018; Mokbal et al. 2019; Tekerek 2021) đạt độ chính xác cao trên tập công khai nhưng vẫn dính tấn công đối kháng vì ánh xạ payload → vector rời rạc. Chen et al. (2022) dùng SAC và 27 đột biến, báo Escape Rate (ER) > 90% trên MLP/LSTM/CNN; dataset ~90k không công khai."),
  p("Pasini, Maragliano, Kim, Tonella (JSS 2026) tái lập Chen trên Mereani, PPO thay SAC, thêm Oracle FastAPI + BeautifulSoup + `zss` so với payload `\"abc\"`. Họ kết luận TH1 (mutation phá XSS) nhẹ (~6–7%), TH2 (preprocess/OOV) là thủ phạm (RR(V) ~93–98%). Khi Oracle vào train, ER vẫn > 96%."),
  h2("1.2. Vấn đề"),
  p("Hai lỗ hổng khiến số ER 99% dễ bị đọc sai. Thứ nhất, Oracle DOM-diff gọi HTML injection là XSS: `<div>hello</div>` cũng “độc” vì đổi cây. 23,4% nhãn Malicious Mereani chỉ đổi DOM, không chạy JavaScript. Thứ hai, artifact `LabelEncoder.fit_transform` từng payload làm token-id không ổn định; agent học lối OOV `None` chứ không sinh XSS còn chạy."),
  h2("1.3. Mục tiêu và đóng góp"),
  p("Luận văn **không** invent generator XSS mới. Ba đóng góp:"),
  p("Tái lập đúng artifact pin `a299bb6` và split `data/10`: Table 4 trùng; ER ~99% và RQ3 ER > 96% lặp lại được với Oracle DOM.", { num: { reference: "contrib", level: 0 } }),
  p("Siết Oracle thành thực thi JS (JSDOM + Playwright hold-out) và khép token-id: chứng minh ER 99% biến mất khi đóng TH2.", { num: { reference: "contrib", level: 0 } }),
  p("Đo CRS 4 (paranoia 1–2) và DOMPurify bằng TASR = #BYPASS_EXEC / N, không lấy HTTP 200 làm thành công.", { num: { reference: "contrib", level: 0 } }),
  h2("1.4. Phạm vi và câu cấm"),
  p("Localhost; Mereani / `data/10`; CRS lab. Không đánh WAF cloud, không LLM payload, không tuyên bố “reproduced Chen 99%”, không replication SAC, không coi ER nhánh A là thành công của luận văn."),
  h2("1.5. Cấu trúc"),
  p("Chương 2 trình bày cơ sở và công thức. Chương 3 mô tả hai nhánh thí nghiệm. Chương 4 báo kết quả. Chương 5–6 thảo luận và hạn chế. Chương 7 kết luận. Phụ lục A là câu được/cấm khi bảo vệ; Phụ lục B là đường dẫn số liệu và lệnh."),
);

// ===== CHƯƠNG 2 =====
children.push(
  h1("Chương 2. Cơ sở lý thuyết và công trình liên quan"),
  h2("2.1. XSS và phát hiện bằng học sâu"),
  p("Phát hiện XSS bằng đặc trưng thủ công rồi học máy (Mereani và Howe, 2018) được thay dần bằng mạng sâu: Fang et al. (DeepXSS, 2018) dùng Word2Vec+LSTM; Mokbal et al. (2019), Tekerek (2021) báo cáo độ chính xác > 97% trên tập công khai. Detector học sâu vẫn dính tấn công đối kháng vì ánh xạ payload → vector rời rạc."),
  h2("2.2. Tấn công đối kháng XSS bằng RL"),
  p("Fang et al. (2018) dùng Dueling DQN, Escape Rate dưới 10%. Zhang et al. (2020) dùng MCTS, chiến lược thoát hạn chế, chi phí cao. Wang et al. (2022) soft Q-learning, ER khoảng 85%. Chen et al. (2022) dùng SAC, 27 đột biến (Table 2), preprocess giữ 10% token phổ biến, ER > 90% trên MLP/LSTM/CNN và công cụ thương mại. Dataset ~90k của Chen không công khai (mối đe dọa TH3 của Pasini)."),
  h2("2.3. Pasini et al. (2026) — khung đánh giá"),
  p("Pasini et al. tái lập Chen trên Mereani, PPO thay SAC (SB3 SAC chỉ continuous), sigmoid thay softmax, Oracle FastAPI+Jinja `|safe` + BeautifulSoup + `zss` so với payload `\"abc\"`. Ba RQ (PDF v2):"),
  p("**RQ1 / TH1:** đột biến có phá XSS không? `RR(E)` trên tập lọt detector.", { num: { reference: "rq", level: 0 } }),
  p("**RQ2 / TH2:** preprocess/OOV có phá XSS không? `RR(V)`, `OR(V)`.", { num: { reference: "rq", level: 0 } }),
  p("**RQ3:** nhét Oracle vào reward thì ER còn cao không?", { num: { reference: "rq", level: 0 } }),
  p("Họ kết luận TH1 nhẹ (~6–7%), TH2 là thủ phạm (`RR(V)` ~93–98%, `OR(V)` ~44–47%). Khi Oracle vào train, ER vẫn > 96% và `RR(V)` ~0."),
  h2("2.4. Công thức"),
  mathPara([
    new MathRun("ER = "),
    new MathFraction({
      numerator: [new MathRun("# độc detector gọi lành")],
      denominator: [new MathRun("|adversarial|")],
    }),
  ]),
  mathPara([
    new MathRun("O(p) = 1  nếu Oracle = Malicious,    RR(M) = 1 − "),
    new MathFraction({
      numerator: [new MathRun("Σ O(m)")],
      denominator: [new MathRun("|M|")],
    }),
  ]),
  mathPara([
    new MathRun("OR(V) = "),
    new MathFraction({
      numerator: [new MathRun("# token None")],
      denominator: [new MathRun("|V|")],
    }),
  ]),
  p("Lab CRS dùng thêm:"),
  p("**Escape** = tỉ lệ HTTP 200 (phụ, không phải thành công).", { num: { reference: "crsmet", level: 0 } }),
  p("**TASR** = `#BYPASS_EXEC / N` (chính; ER có oracle thực thi).", { num: { reference: "crsmet", level: 0 } }),
  p("**Δ** = Escape − TASR (khoảng TH2: lọt HTTP nhưng hết độc).", { num: { reference: "crsmet", level: 0 } }),
  p("Ba nhãn: `BLOCK` | `BYPASS_NOEXEC` | `BYPASS_EXEC`. Chỉ TASR được viết là tấn công thành công."),
  h2("2.5. Chuỗi Evidence → Finding → Path"),
);
children.push(
  table(
    [700, 2800, 2785, 2786],
    ["ID", "Evidence", "Finding", "Path"],
    [
      ["E1", "filter_report.json: 3542/15149 (23,4%) Malicious Mereani chỉ đổi DOM, không execute JSDOM", "Oracle BeautifulSoup+zss không tương đương XSS", "Lọc lab bằng oracle thực thi; RR gốc = 0 trên 10824 mẫu"],
      ["E2", "mutators.py @ a299bb6: A18 return payload, A20 stub, A21 alert(1) → (1)(1)", "Table 2 paper ≠ code", "Lab viết lại 27 action; không import mutators.py vào train luận văn"],
      ["E3", "LabelEncoder.fit_transform từng payload; Table 4 lab trùng 99,67/100/99,83", "Ba mạng một bộ số; token-id không ổn định", "Nhánh A giữ bug để tái lập ER ~99%; nhánh B khép encode"],
      ["E4", "Nhánh A data/10: LSTM ER 98,78%, RR(V) 98,54%, OR(V) 48,5%", "Tái lập replication + TH2 trên đúng split Pasini", "Viết “protocol lặp lại được”, không “reproduced Chen 99%”"],
      ["E5", "Nhánh A RQ3 LSTM+Oracle: ER 98,34%, RR = 0, OR(V) 1,69%", "Claim Pasini RQ3 lặp lại được với Oracle DOM", "Không đồng nhất với XSS còn chạy JS"],
      ["E6", "Nhánh B P3: LSTM acc 0,991; PPO 3×20k ER tb 0,75%", "Khi khép OOV, ER 99% biến mất; TH2 còn nhưng hiếm", "Không viết replication ER 99% trên lab JSDOM"],
      ["E7", "Nhánh B P4: PPO ER=TASR=0,25%; Dueling DQN 1,08%; RR=0", "Oracle execute kéo ER về sàn FN", "Bảng PPO vs DDQN; không khoe thuật toán"],
      ["E8", "P5 CRS PL1: catalog Table 2/mở rộng = 0 BYPASS_EXEC; DOMPurify Δ=1", "WAF không dính None; lọt HTTP ≠ còn độc", "TASR bắt buộc; không train RL trên CRS"],
    ]
  ),
  cap("Bảng 2.1. Evidence → Finding → Path (số đã chốt từ lab)"),
);

// ===== CHƯƠNG 3 =====
children.push(
  h1("Chương 3. Phương pháp"),
  h2("3.1. Hai nhánh thí nghiệm (không trộn số)"),
  p("Pipeline bắt buộc: payload độc (RR gốc = 0) → agent chọn 1/27 action Table 2 → detector → tập E (ER) → Oracle E cho RR(E) (RQ1) → preprocess thành V cho OR(V) (RQ2) → train lại, reward âm nếu hết độc → ER′ và TASR (RQ3)."),
);
children.push(
  table(
    [1800, 2271, 2500, 2500],
    ["Nhánh", "Dataset / encode", "Oracle", "Mục tiêu"],
    [
      ["A — sát Pasini", "Artifact data/10 (Table 3). LabelEncoder.fit_transform từng mẫu", "DOM-diff vs “abc”", "Tái lập ER ~99% và RQ3"],
      ["B — luận văn", "Mereani lọc JSDOM, split kiểu Table 3. id cố định theo vocab", "JSDOM hook + Playwright hold-out", "Khép TH2; đo TASR trên CRS"],
    ]
  ),
  cap("Bảng 3.1. Hai nhánh — cùng 27 mô tả Table 2, khác encode và Oracle"),
  p("Nhánh A dùng `mutators.py` (kể cả A18 no-op, A21 `(1)(1)`). Nhánh B dùng `lab/src/actions.py` (A18/A20/A21 làm đúng). Không trộn ER ~99% với ER ~0,75%."),
  h2("3.2. Khác biệt Chen / Pasini / luận văn"),
);
children.push(
  table(
    [1600, 2490, 2491, 2490],
    ["Hạng mục", "Chen 2022", "Pasini 2026", "Luận văn"],
    [
      ["Dataset", "XSSed+Alexa ~90k, không public", "Mereani + Oracle DOM, undersample", "Tập A: Mereani JSDOM; nhánh A: đúng data/10"],
      ["Detector", "MLP LSTM CNN + SafeDog/XSSChop", "MLP LSTM CNN", "A: đủ 3 mạng. B: LSTM + CRS PL1/PL2 + DOMPurify"],
      ["Agent", "SAC", "PPO SB3", "PPO (replication) và Dueling DQN"],
      ["State", "lịch sử action", "lịch sử action (code)", "Giữ lịch sử action như paper"],
      ["Reward", "+10 / −1", "PDF −2 nếu vỡ; code −5", "A: đúng code −5. B: R_exec (−2 hết độc; +10 chỉ khi lọt và execute)"],
      ["Oracle", "không", "BS4 + zss", "A: như paper. B: JSDOM; Playwright 4 seed"],
      ["Metric", "ER", "ER + RR + OR", "A: ER/RR/OR. B: TASR + Δ"],
      ["Action", "27 mô tả", "27, A18/A20/A21 lỗi", "B đủ 27 + parser_alive / browser_alive"],
    ]
  ),
  cap("Bảng 3.2. Chen vs Pasini vs luận văn"),
  p("Lệch protocol nhánh B đã ghi: Adam (SGD kẹt 50% trên split JSDOM); pad 40 (trung vị token = 6; code artifact `MAX_LENGTH=30`, paper viết 200); 3 seed PPO (paper 10); eval agent 400/1084. Nhánh A lệch môi trường, không đổi protocol: `int(embedding_dim)` (PyTorch 2.14); `TemplateResponse` Starlette 1.x."),
  h2("3.3. Oracle"),
  p("**Pasini (nhánh A).** FastAPI nhét payload vào Jinja `|safe`. DummyDetector luôn True. `O(p)=1` khi cây DOM khác trang `\"abc\"`. Hệ quả: `<div>hello</div>` = Malicious. Paper mục 8 tự nhận Oracle “may be subject to misclassification”."),
  p("**Luận văn (nhánh B).** JSDOM `runScripts: dangerously`, hook `alert`/`confirm`/`prompt`/`print`/`eval`/`Function`/`document.title`/`cookie`/`__XSS_ORACLE`. `parser_changed` chỉ tín hiệu phụ. Playwright Chromium hold-out trên 4 seed; không dùng để train."),
  h2("3.4. Dataset và split"),
  p("Mereani `Payloads.csv` (latin-1): 43.217 dòng, 15.149 độc / 28.068 lành."),
  p("Nhánh A: dùng nguyên `filtered_oracle.csv` → `data/10` của artifact. Detector train/val/test 2.883+721+901 mỗi lớp (Benign detector 2.883/721/901). Agent chỉ Malicious 2.883/721/901. Vocab 720 token (10%). Agent val paper ghi 712, CSV artifact là 721 — dùng CSV phát hành."),
  p("Nhánh B: lọc JSDOM. Giữ 10.824 độc execute, loại 3.542 parser-only (W1 = 23,4%), loại 783 không DOM không JS, loại 10 lành false-positive oracle. RR trên tập giữ = 0. Split seed 42, tỉ lệ Table 3: detector 3.463/865/1.084 mỗi lớp; agent 3.463/865/1.084 chỉ độc."),
  h2("3.5. Detector và agent"),
  p("Nhánh A: MLP/LSTM/CNN artifact, embed 8, SGD 1e−3, batch 16, 150 epoch, patience 10, BCE+sigmoid. PPO `MlpPolicy`, 250.000 timesteps, max 15 bước, 27 action. Eval khi train: 32 episode (chọn best_model); test ER trên 901 mẫu agent-test."),
  p("Nhánh B: LSTM embed 8, hidden 128, vocab 1.191, pad 40, Adam 1e−3. PPO 20k × 3 seed (thêm 80k một seed). P4: PPO 3 seed + DQN SB3 1 seed + Dueling DQN 3 seed, `R_exec`."),
  h2("3.6. P5 — CRS và DOMPurify"),
  p("Luồng: payload → CRS PL1 (`:18080`) / PL2 (`:18081`) → (tuỳ chọn) DOMPurify trên app `:13000` → Oracle execute. Paranoia CRS 1 và 2, anomaly inbound 5. Chỉ 127.0.0.1. Không claim WAF cloud."),
  p("Gate trước khi train RL trên CRS: tồn tại ≥ 1 payload Table 2 vừa execute vừa HTTP 200 trên PL1. **Không đạt** → không train RL trên CRS, không LLM payload."),
);

// ===== CHƯƠNG 4 =====
children.push(
  h1("Chương 4. Kết quả"),
  h2("4.1. P1 — Oracle thực thi và Mereani (nhánh B)"),
);
children.push(
  table(
    [6050, 3021],
    ["Hạng mục", "n"],
    [
      ["Mereani gốc", "43.217 (15.149 độc / 28.068 lành)"],
      ["Độc còn execute, giữ", "10.824"],
      ["Độc chỉ đổi DOM, loại (W1)", "3.542 (23,4%)"],
      ["Độc không DOM không JS", "783"],
      ["Lành bị oracle gọi độc", "10"],
      ["RR trên tập độc đã giữ", "0,0"],
    ],
    { aligns: [AlignmentType.LEFT, AlignmentType.CENTER] }
  ),
  cap("Bảng 4.1. Lọc Mereani bằng oracle thực thi"),
  p("Pasini giữ 3.542 mẫu parser-only. Lab loại. Đó là đo W1 trên đúng nguồn Mereani."),
  h2("4.2. P2 — 27 action"),
  p("Khi action thật sự đổi payload (3 seed: `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`, `javascript:` href):"),
  p("Giữ execution: A1, A2, A3, A4, A8, A11, A14, A15, A17, A18, A19, A21, A22, A23, A27.", { num: { reference: "act", level: 0 } }),
  p("Parser sống, JS chết (W8): A5, A6, A7, A12, A13, A20, A25. A9/A24/A26 chết một phần seed.", { num: { reference: "act", level: 0 } }),
  p("A10/A16 no-op trên 3 seed không có `http://` / `data:` — bình thường.", { num: { reference: "act", level: 0 } }),
  p("Lab: A18 không no-op; A21 không `(1)(1)`.", { num: { reference: "act", level: 0 } }),
  h2("4.3. Nhánh A — tái lập sát artifact (data/10, seed 42)"),
  h3("4.3.1. Table 4 — detector"),
  p("Test n = 1.802. Cả ba mạng: TP = 901, FP = 3, TN = 898, FN = 0."),
);
children.push(
  table(
    [2800, 1567, 1568, 1568, 1568],
    ["", "Precision", "Recall", "Accuracy", "F1"],
    [
      ["Paper MLP = LSTM = CNN", "99,67%", "100%", "99,83%", "99,83%"],
      ["Lab LSTM / MLP / CNN", "99,67%", "100%", "99,83%", "99,83%"],
    ],
    { aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER] }
  ),
  cap("Bảng 4.2. Table 4 detector — trùng tới hai chữ số"),
  p("Ba mạng một bộ số = W4 đo được, không phải copy bảng."),
  h3("4.3.2. PPO không Oracle (250k bước, test 901)"),
);
children.push(
  table(
    [1815, 1814, 1814, 1814, 1814],
    ["", "ER paper", "ER lab", "RR(E) paper", "RR(E) lab"],
    [
      ["LSTM", "98,62%", "98,78% (890/901)", "6,34%", "8,99%"],
      ["MLP", "99,73%", "98,67%", "7,07%", "10,24%"],
      ["CNN", "98,25%", "98,89%", "6,36%", "0%"],
    ],
    { aligns: Array(5).fill(AlignmentType.CENTER) }
  ),
  cap("Bảng 4.3a. Replication PPO — Escape Rate và RR(E)"),
);
children.push(
  table(
    [1800, 1818, 1818, 1817, 1818],
    ["", "RR(V) paper", "RR(V) lab", "OR(V) paper", "OR(V) lab"],
    [
      ["LSTM", "97,31%", "98,54%", "47,49%", "48,54%"],
      ["MLP", "97,84%", "98,54%", "44,76%", "45,01%"],
      ["CNN", "92,57%", "1,35%", "43,85%", "2,42%"],
    ],
    { aligns: Array(5).fill(AlignmentType.CENTER) }
  ),
  cap("Bảng 4.3b. Replication PPO — RR(V) và OR(V) (TH2)"),
  p("LSTM/MLP khớp TH2 (OOV cao). CNN seed 42 vẫn ER ~99% nhưng ít `None` (spam `<script>`, LabelEncoder vẫn lệch id) — phương sai 1 seed, không fail ER."),
  p("Val LSTM: reward −8,57 @ 25k → ~5,8 từ 50k đến 250k. Entropy 3,29 → 0,16. LSTM PPO không Oracle thêm seed 43/44 (50k): ER 97,34% / 96,56%. Trung bình 3 seed **97,56%** so với paper 98,62% (10 seed)."),
  h3("4.3.3. RQ3 — Oracle-in-loop (code −5), test 901"),
);
children.push(
  table(
    [3200, 1957, 1957, 1957],
    ["", "ER paper", "ER lab", "RR(V) lab"],
    [
      ["LSTM 250k seed 42", "98,13%", "98,34%", "0"],
      ["MLP 250k seed 42", "97,37%", "97,89%", "0"],
      ["CNN 250k seed 42", "96,89%", "96,00%", "0,12%"],
    ],
    { aligns: Array(4).fill(AlignmentType.CENTER) }
  ),
  cap("Bảng 4.4. RQ3 Oracle-in-loop, seed 42, 250k bước. CNN 50k đã 96,00%; 250k không đổi test set."),
  p("Câu được: *Trên đúng artifact và split `data/10`, tái lập ER ~99% (replication), RR(V)~98% (TH2), và RQ3 LSTM/MLP/CNN ER>96% với RR≈0 theo Oracle DOM.*"),
  p("Câu cấm: coi ER 99% sau Oracle DOM là XSS còn chạy JavaScript."),
  h2("4.4. Nhánh B P3 — LSTM + PPO, encode ổn định"),
  p("LSTM test n = 2.168: acc **0,991**, Precision 0,990, Recall 0,992, F1 0,991. FN không đột biến 400 mẫu: **0,25%**."),
);
children.push(
  table(
    [1200, 1400, 1400, 1600, 1600, 1871],
    ["Seed", "Bước", "Escape", "ER", "RR(E)", "OR(V) trên E"],
    [
      ["42", "20k", "1", "0,25%", "0", "0,75"],
      ["43", "20k", "2", "0,50%", "0", "0,28"],
      ["44", "20k", "6", "1,50%", "0,33", "0,40"],
      ["45", "80k", "8", "2,00%", "0,12", "0,43"],
    ],
    { aligns: Array(6).fill(AlignmentType.CENTER) }
  ),
  cap("Bảng 4.5. PPO nhánh B — không Oracle trong reward"),
  p("ER trung bình 3 seed × 20k = **0,75%**. 80k → 2%. Pasini artifact > 96%. Khi khép token-id và action giữ XSS, PPO Table 2 không còn ER ~99%. Escape còn lại mang OOV cao — TH2 vẫn tồn tại nhưng hiếm."),
  h2("4.5. Nhánh B P4 — Oracle-in-loop và PPO vs Dueling DQN"),
);
children.push(
  table(
    [2800, 1600, 1557, 1557, 1557],
    ["Agent", "Oracle train", "ER", "TASR", "RR(E)"],
    [
      ["P3 PPO, 3 seed", "không", "0,75%", "~0,58%", "0–0,33"],
      ["P4 PPO + R_exec, 3 seed", "có", "0,25%", "0,25%", "0"],
      ["P4 DQN SB3, seed 42", "có", "0,25%", "0,25%", "0"],
      ["P4 Dueling DQN, 3 seed", "có", "1,08%", "1,08%", "0"],
      ["Sàn FN detector", "—", "0,25%", "0,25%", "0"],
    ],
    { aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER] }
  ),
  cap("Bảng 4.6. PPO vs Dueling DQN trên LSTM đã khép OOV"),
  p("Dueling DQN từng seed: 1,75% / 0,75% / 0,75%. Wilcoxon P3 vs P4 PPO: n = 2, p = 0,5 — chỉ mô tả, P4 ≤ P3 mọi seed, không tuyên bố ý nghĩa thống kê."),
  p("Trên LSTM đã khép OOV, `R_exec` kéo ER về sàn FN. Không tái lập RQ3 ER>96% của Pasini **khi Oracle là thực thi JS**."),
  h2("4.6. Đối chiếu hai nhánh"),
);
children.push(
  table(
    [2800, 3135, 3136],
    ["", "Nhánh A data/10 + LabelEncoder", "Nhánh B JSDOM + id cố định"],
    [
      ["LSTM acc", "99,83%", "99,1%"],
      ["PPO không Oracle ER", "98,78%", "0,75%"],
      ["PPO + Oracle ER", "98,34%", "0,25%"],
      ["RR(V) không Oracle", "98,54%", "ít escape; OR trên E 28–75%"],
      ["RR sau Oracle-in-loop", "0 (Oracle DOM)", "0 (Oracle JS)"],
    ]
  ),
  cap("Bảng 4.7. Cùng protocol, khác encode"),
  p("ER 99% là artifact encode/OOV, không phải tấn công XSS ổn định."),
  h2("4.7. P5 — CRS, DOMPurify, transfer, Playwright"),
);
children.push(
  table(
    [5000, 1800, 2271],
    ["Thí nghiệm", "n", "TASR CRS PL1"],
    [
      ["3 seed × 27 action /html", "84", "0"],
      ["Cặp 2 action", "672", "0"],
      ["Bộ ba keeper", "686", "0"],
      ["Mereani decode × Table 2", "1.120", "0"],
      ["Transfer PPO P3/P4", "80", "0"],
      ["TAP-B + E1–E10", "60", "0"],
    ],
    { aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER] }
  ),
  cap("Bảng 4.8. TASR trên CRS paranoia 1"),
  p("Cùng 84 payload `/html`: App không WAF TASR **0,845**, Δ = 0,155. DOMPurify TASR **0**, Δ = **1,00** (lọt HTTP, hết độc)."),
  p("Transfer LSTM-agent → CRS: PL1/PL2 TASR = 0. App TASR P4 = 0,0125 vì Mereani nhiều URL, khác seed `<script>`."),
  p("Playwright: `<script>alert(1)`, `<img onerror>`, `javascript:` href execute; `<div>hello</div>` không — khớp JSDOM trên seed. Không có mẫu Chromium-qua-WAF. Gate `BYPASS_EXEC` PL1 **không đạt**. Không train RL trên CRS."),
  p("Câu được: *Trên lab CRS 4 paranoia 1, catalog Chen/Pasini và PPO train LSTM có TASR = 0. WAF không dính OOV-None.*"),
);

// ===== CHƯƠNG 5-7 =====
children.push(
  h1("Chương 5. Thảo luận"),
  p("Pasini sửa Chen đúng hướng: phải đo payload còn độc. Oracle DOM của họ vẫn gọi HTML injection là XSS (E1). `RR(V)` trên chuỗi đã thay `None` gần tautology (W2). Nhánh A chứng minh: giữ nguyên bug encode thì số paper lặp lại được. Nhánh B chứng minh: khép bug thì ER sụp. CRS chứng minh: detector không dính `None` thì Table 2 không tạo BYPASS_EXEC."),
  p("Đóng góp so paper: oracle thực thi; catalog 27 action làm đủ; TASR/Δ trên CRS+DOMPurify; bảng PPO vs Dueling DQN trên detector đã khép OOV."),
  p("Không đóng góp: generator XSS mới; bypass CRS; đánh WAF cloud."),
  h1("Chương 6. Hạn chế (threats to validity)"),
  p("JSDOM không phủ mọi XSS (mXSS, DOM clobbering, sink framework). Playwright chỉ 4 seed.", { num: { reference: "lim", level: 0 } }),
  p("Mereani 2018: `alert` / `<script>`; TAP-B không làm LSTM vỡ (FN = 0 trên 17 mẫu chạy).", { num: { reference: "lim", level: 0 } }),
  p("Table 2 lỗi thời (`vbscript`, `%00`). A10/A16 no-op trên seed không URL.", { num: { reference: "lim", level: 0 } }),
  p("Nhánh A: chủ yếu seed 42 (paper 10 seed). CNN RR(V) lệch trung bình paper.", { num: { reference: "lim", level: 0 } }),
  p("Nhánh B: 3 seed, eval 400, pad 40, Adam. Wilcoxon n = 2 vô nghĩa thống kê.", { num: { reference: "lim", level: 0 } }),
  p("State MDP chưa nhúng payload (giữ như paper).", { num: { reference: "lim", level: 0 } }),
  p("Histogram action P4: một escape = sàn FN, không kết luận policy dùng A1/A6–A13.", { num: { reference: "lim", level: 0 } }),
  p("CRS paranoia 1–2 lab, không phải rule set production hay WAF nhà cung cấp.", { num: { reference: "lim", level: 0 } }),
  h1("Chương 7. Kết luận"),
  p("Khung Pasini (Oracle → RR → Oracle-in-loop) là đúng chỗ bám.", { num: { reference: "conc", level: 0 } }),
  p("Trên đúng `data/10` và code artifact, ER ~99% và RQ3 ER ~98% **tái lập được**.", { num: { reference: "conc", level: 0 } }),
  p("Thủ phạm là token-id không ổn định + OOV `None` (TH2), không phải “RL sinh XSS mạnh”.", { num: { reference: "conc", level: 0 } }),
  p("Khi encode ổn định và Oracle là thực thi JS, PPO/DDQN Table 2 về sàn FN (~0,25–1,08%), RR = 0.", { num: { reference: "conc", level: 0 } }),
  p("CRS/DOMPurify: TASR = 0 trên catalog Chen/Pasini; Δ Purify = 1. Không train RL khi chưa có primitive BYPASS_EXEC.", { num: { reference: "conc", level: 0 } }),
);

// ===== PHỤ LỤC A =====
children.push(
  h1("Phụ lục A. Câu được viết / câu cấm"),
  h2("A.1. Được viết"),
);
["Khung đánh giá theo Pasini et al. (2026): mẫu đối kháng phải còn độc theo oracle thực thi.",
  "23,4% nhãn Malicious Mereani chỉ đổi DOM — Oracle BeautifulSoup không tương đương XSS.",
  "Trên artifact data/10, PPO tái lập ER ~99% và RQ3 ER 98,3% với RR = 0 theo Oracle DOM.",
  "Khi khép token-id, PPO Table 2 không còn ER ~99%; escape còn lại mang OOV cao.",
  "Trên LSTM đã khép OOV, PPO ER = TASR = 0,25%, Dueling DQN 1,08%, RR(E) = 0.",
  "Trên lab CRS 4 PL1, catalog Chen/Pasini có TASR = 0.",
].forEach((t) => children.push(p(t, { num: { reference: "ok", level: 0 } })));
children.push(h2("A.2. Cấm viết"));
["Replication thành công ER Chen 99% như thành công của luận văn.",
  "“Reproduced Chen’s numbers”; replication SAC.",
  "PPO/DQN mạnh hơn Chen.",
  "Bypass CRS; đánh AWS WAF / WAF cloud.",
  "CRS 200 = TASR; dùng LLM sinh payload.",
  "Wilcoxon p = 0,5 như khác biệt có ý nghĩa.",
  "RQ1–RQ4 theo HTML cũ thay PDF v2.",
].forEach((t) => children.push(p(t, { num: { reference: "no", level: 0 } })));

// ===== TÀI LIỆU =====
children.push(
  h1("Tài liệu tham khảo"),
  p("Pasini, S., Maragliano, G., Kim, J., Tonella, P. (2026). Cross-site scripting adversarial attacks based on deep reinforcement learning: Evaluation and extension study. Journal of Systems and Software. DOI: 10.1016/j.jss.2026.112856. arXiv:2502.19095."),
  p("Chen, L., Tang, C., He, J., Zhao, H., Lan, X., Li, T. (2022). XSS adversarial example attacks based on deep reinforcement learning. Computers & Security 120:102831."),
  p("Mereani, F.A., Howe, J.M. (2018). Detecting cross-site scripting attacks using machine learning. AMLTA 2018."),
  p("Fang, Y., Li, Y., Liu, L., Huang, C. (2018). DeepXSS: Cross site scripting detection based on deep learning."),
  p("Wang, Y. et al. (2022). Soft Q-learning XSS adversarial examples. Computers & Security 113:102554."),
  p("Zhang et al. (2020). MCTS for XSS adversarial examples. IEEE Access."),
  p("Schulman, J. et al. (2017). Proximal Policy Optimization Algorithms. arXiv:1707.06347."),
  p("Haarnoja, T. et al. (2018). Soft Actor-Critic. arXiv:1801.01290."),
  p("OWASP ModSecurity Core Rule Set (CRS) 4. Lab paranoia 1–2, không phải đánh giá nhà cung cấp WAF."),
  p("Cure53 DOMPurify. Đo Δ = Escape − TASR trên app lab."),
);

// ===== PHỤ LỤC B =====
children.push(
  h1("Phụ lục B. File số liệu và lệnh"),
);
children.push(
  table(
    [3200, 5871],
    ["Nội dung", "File"],
    [
      ["Replication data/10", "lab/data/PASINI_FAITHFUL_RESULTS.md"],
      ["P1 P2", "lab/data/P1_P2_RESULTS.md"],
      ["P3", "lab/data/P3_RESULTS.md"],
      ["P4", "lab/data/P4_RESULTS.md"],
      ["PPO vs DDQN", "lab/data/PPO_VS_DDQN.md"],
      ["P5", "lab/data/P5_RESULTS.md"],
      ["Checkpoint nhánh A", "artifact/Adversarial_RL_XSS/runs/{lstm,mlp,cnn}/10/run_0/"],
      ["Checkpoint nhánh B", "lab/runs/p3/, lab/runs/p4/"],
      ["Nguồn dán Word", "huong_dan/2026-09-17_luan-van-P6.md"],
    ]
  ),
  cap("Bảng B.1. Đường dẫn số liệu"),
  new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text: "Lệnh kiểm tra (nhánh B)", font: FONT, size: 24, bold: true })],
  }),
  p("cd lab", { font: "Courier New", size: 20, align: AlignmentType.LEFT, after: 40 }),
  p("../.venv/bin/python -m unittest tests.test_oracle tests.test_actions -v", { font: "Courier New", size: 20, align: AlignmentType.LEFT, after: 40 }),
  p("../.venv/bin/python src/run_p3.py --phase eval --ppo-seeds 42,43,44 --max-eval 400", { font: "Courier New", size: 20, align: AlignmentType.LEFT, after: 40 }),
  p("../.venv/bin/python src/run_p4.py --phase eval --algo ppo,dqn --seeds 42,43,44 --max-eval 400", { font: "Courier New", size: 20, align: AlignmentType.LEFT, after: 40 }),
  p("../.venv/bin/python src/measure_tasr.py --sink /html", { font: "Courier New", size: 20, align: AlignmentType.LEFT, after: 80 }),
  p("Nhánh A (đã chạy): `bash lab/src/run_pasini_faithful.sh eval-lstm`."),
);

const page = {
  size: { width: 11906, height: 16838 },
  margin: { top: 1417, right: 1134, bottom: 1134, left: 1701 },
};

const doc = new Document({
  creator: "ATBMHTTT lab",
  title: "Luận văn ATBMHTTT — Pasini 2026 XSS adversarial RL",
  description: "Các chương luận văn dán Word. Số đã chốt từ lab.",
  styles: {
    default: { document: { run: { font: FONT, size: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: NAVY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: NAVY },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, italics: true, font: FONT },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "contrib", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "rq", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "crsmet", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "act", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "lim", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "conc", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "ok", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "no", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [
    {
      properties: {
        titlePage: true,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1417, right: 1134, bottom: 1134, left: 1701 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY, space: 4 } },
          children: [new TextRun({ text: "ATBMHTTT — Pasini 2026", font: FONT, size: 18, italics: true, color: NAVY })],
        })] }),
        first: new Header({ children: [new Paragraph({ children: [] })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: "BFBFBF", space: 4 } },
          children: [
            new TextRun({ text: "Trang ", font: FONT, size: 18 }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 }),
          ],
        })] }),
        first: new Footer({ children: [new Paragraph({ children: [] })] }),
      },
      children,
    },
  ],
});

const out = "/home/kali/Desktop/ATBMHTTT/huong_dan/Luan_van_ATBMHTTT_Pasini_2026.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length);
}).catch((e) => {
  console.error(e);
  process.exit(1);
});
