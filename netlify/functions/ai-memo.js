const admin = require("firebase-admin");

let firebaseApp;
function getFirebaseApp() {
  if (!firebaseApp) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    firebaseApp = admin.initializeApp({
      credential: admin.credential.cert(serviceAccount)
    });
  }
  return firebaseApp;
}

// テーマキー -> AIへの指示内容（プロンプトに使用）
const THEME_PROMPTS = {
  history: "その土地の歴史的背景・史跡",
  language: "現地で使われている言語、簡単なあいさつ・言い回し",
  shops: "具体的な店名を含むおすすめのレストラン・ショップ",
  spots: "定番から少し外れた訪れる価値のある場所",
  transport: "電車・バス・タクシー事情、ICカードなど",
  safety: "治安状況、物価感（食事・交通などの目安）、旅行者が気をつけるべき点",
  food_culture: "食文化、チップ習慣、食事マナーなど（おすすめのお店とは別観点）",
  events: "旅行期間に合った現地のイベント・祭り"
};

function tripContextText(body) {
  const lines = [];
  if (body.destination) lines.push("旅行先: " + body.destination);
  if (Array.isArray(body.regions) && body.regions.length) lines.push("地域: " + body.regions.join("、"));
  lines.push("旅行種別: " + (body.type === "domestic" ? "国内旅行" : "海外旅行"));
  if (body.startDate) lines.push("旅行期間: " + body.startDate + (body.endDate ? " 〜 " + body.endDate : ""));
  return lines.join("\n");
}

function resp(statusCode, bodyObj) {
  return {
    statusCode: statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj)
  };
}

async function callGemini(prompt, opts) {
  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + process.env.GEMINI_API_KEY;

  const generationConfig = { maxOutputTokens: opts.maxOutputTokens || 500 };
  if (opts.responseMimeType) generationConfig.responseMimeType = opts.responseMimeType;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: generationConfig
    })
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error("Gemini API error: " + res.status + " " + errBody);
  }

  const data = await res.json();
  const text = data && data.candidates && data.candidates[0] && data.candidates[0].content &&
    data.candidates[0].content.parts && data.candidates[0].content.parts[0] &&
    data.candidates[0].content.parts[0].text;
  if (!text) throw new Error("Gemini API returned no text");
  return text;
}

async function handleThemes(body) {
  const themes = Array.isArray(body.themes) ? body.themes.filter(function (t) { return THEME_PROMPTS[t]; }) : [];
  if (themes.length === 0) return resp(400, { error: "themesが不正です" });

  const context = tripContextText(body);
  const instructions = themes.map(function (key) {
    return "- " + key + ": " + THEME_PROMPTS[key];
  }).join("\n");

  const prompt = context + "\n\n" +
    "上記の旅行に関する情報をもとに、以下の各テーマについて日本語で150〜250文字程度で説明してください。\n" +
    instructions + "\n\n" +
    "出力は必ず次のJSON形式のみで返してください（説明文や前置き、コードブロック記号は不要）:\n" +
    '{"results":[{"theme":"テーマキー","text":"本文"}]}';

  const maxTokens = themes.length * 300;
  const raw = await callGemini(prompt, { responseMimeType: "application/json", maxOutputTokens: maxTokens });

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return resp(500, { error: "AIの応答を解析できませんでした" });
  }
  if (!parsed || !Array.isArray(parsed.results)) {
    return resp(500, { error: "AIの応答を解析できませんでした" });
  }
  return resp(200, { results: parsed.results });
}

async function handleQuestion(body) {
  const question = (body.question || "").trim();
  if (!question) return resp(400, { error: "questionが不正です" });

  const context = tripContextText(body);
  const prompt = context + "\n\n" +
    "上記の旅行に関する次の質問に、日本語で200〜300文字程度で回答してください。\n" +
    "質問: " + question;

  const text = await callGemini(prompt, { maxOutputTokens: 500 });
  return resp(200, { answer: text.trim() });
}

exports.handler = async function (event) {
  if (event.httpMethod !== "POST") {
    return resp(405, { error: "Method Not Allowed" });
  }

  if (!process.env.FIREBASE_SERVICE_ACCOUNT || !process.env.GEMINI_API_KEY) {
    return resp(500, { error: "サーバー設定が不完全です" });
  }

  const authHeader = event.headers.authorization || event.headers.Authorization || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (!token) return resp(401, { error: "認証が必要です" });

  try {
    await getFirebaseApp().auth().verifyIdToken(token);
  } catch (e) {
    return resp(401, { error: "認証が必要です" });
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch (e) {
    return resp(400, { error: "リクエストの形式が正しくありません" });
  }

  try {
    if (body.mode === "themes") return await handleThemes(body);
    if (body.mode === "question") return await handleQuestion(body);
    return resp(400, { error: "modeが不正です" });
  } catch (e) {
    console.error(e);
    return resp(500, { error: "AI生成に失敗しました" });
  }
};
