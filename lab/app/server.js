"use strict";

const express = require("express");
const { JSDOM } = require("jsdom");
const createDOMPurify = require("dompurify");
const purifyVersion = "3.2.4";

const PORT = Number(process.env.PORT || 3000);
const { window } = new JSDOM("", { url: "http://lab.local/" });
const DOMPurify = createDOMPurify(window);

const ORACLE_HOOK = `<script>
window.__XSS_ORACLE = false;
(function () {
  function trip() {
    window.__XSS_ORACLE = true;
    try { document.title = "XSS_ORACLE"; } catch (e) {}
  }
  ["alert", "prompt", "confirm"].forEach(function (name) {
    var orig = window[name];
    window[name] = function () {
      trip();
      if (typeof orig === "function") {
        try { return orig.apply(window, arguments); } catch (e) {}
      }
    };
  });
})();
</script>`;

function page(title, inner) {
  return (
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">" +
    "<title>" +
    title +
    "</title>" +
    ORACLE_HOOK +
    "</head><body>" +
    inner +
    "</body></html>"
  );
}

function qOf(req) {
  const v = req.query.q;
  if (v === undefined || v === null) return "";
  return Array.isArray(v) ? String(v[0]) : String(v);
}

function renderHtml(q) {
  return page("lab-html", '<p id="ctx">html_body</p><div id="out">' + q + "</div>");
}

function renderAttr(q) {
  return page(
    "lab-attr",
    '<p id="ctx">attr</p><form><input id="x" name="n" value="' + q + '"></form>'
  );
}

function renderJs(q) {
  return page(
    "lab-js",
    '<p id="ctx">js_string</p><script>var s = \'' + q + "';</script>"
  );
}

const app = express();
app.disable("x-powered-by");
app.set("etag", false);

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "xss-lab-app",
    dompurify: purifyVersion,
    routes: [
      "/html?q=",
      "/attr?q=",
      "/js?q=",
      "/purify/html?q=",
      "/purify/attr?q=",
      "/purify/js?q=",
    ],
  });
});

app.get("/html", (req, res) => {
  res.type("html").send(renderHtml(qOf(req)));
});
app.get("/attr", (req, res) => {
  res.type("html").send(renderAttr(qOf(req)));
});
app.get("/js", (req, res) => {
  res.type("html").send(renderJs(qOf(req)));
});

app.get("/purify/html", (req, res) => {
  res.type("html").send(renderHtml(DOMPurify.sanitize(qOf(req))));
});
app.get("/purify/attr", (req, res) => {
  res.type("html").send(renderAttr(DOMPurify.sanitize(qOf(req))));
});
app.get("/purify/js", (req, res) => {
  res.type("html").send(renderJs(DOMPurify.sanitize(qOf(req))));
});

app.use((_req, res) => {
  res.status(404).type("text").send("not found");
});

app.listen(PORT, "0.0.0.0", () => {
  process.stdout.write("xss-lab-app listen " + PORT + "\n");
});
