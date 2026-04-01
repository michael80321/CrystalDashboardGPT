import datetime as dt
import io
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="每日水晶戰情室看板", layout="wide")


@dataclass
class NewsTopic:
    label: str
    query: str


TW_TOP20_DEFAULT = [
    "友商01（請替換）", "友商02（請替換）", "友商03（請替換）", "友商04（請替換）", "友商05（請替換）",
    "友商06（請替換）", "友商07（請替換）", "友商08（請替換）", "友商09（請替換）", "友商10（請替換）",
    "友商11（請替換）", "友商12（請替換）", "友商13（請替換）", "友商14（請替換）", "友商15（請替換）",
    "友商16（請替換）", "友商17（請替換）", "友商18（請替換）", "友商19（請替換）", "友商20（請替換）",
]

DEFAULT_COMPETITOR_CSV = """competitor,ig_account,website
友商01（請替換）,https://www.instagram.com/example_1,https://example.com
友商02（請替換）,https://www.instagram.com/example_2,https://example.org
友商03（請替換）,https://www.instagram.com/example_3,https://example.net
"""

DEFAULT_POST_CSV = """date,competitor,platform,post_text,product,likes,comments,shares,clicks
2026-03-30,友商01（請替換）,IG,新品白水晶手鍊限時優惠,白水晶手鍊,460,92,38,1280
2026-03-30,友商02（請替換）,IG,紫水晶洞開箱直播,紫水晶洞,520,140,60,1750
2026-03-31,友商03（請替換）,官網,月光石項鍊新品上架,月光石項鍊,300,24,20,2100
2026-04-01,友商01（請替換）,IG,招財黃水晶居家擺件推薦,黃水晶擺件,640,188,90,2420
"""


@st.cache_data(ttl=60 * 30)
def fetch_google_news(query: str, hl: str = "zh-TW", gl: str = "TW", ceid: str = "TW:zh-Hant", limit: int = 12) -> pd.DataFrame:
    q = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        rows = []
        for item in root.findall("./channel/item")[:limit]:
            rows.append(
                {
                    "title": item.findtext("title", default="").strip(),
                    "link": item.findtext("link", default="").strip(),
                    "pubDate": item.findtext("pubDate", default="").strip(),
                    "source": item.findtext("source", default="").strip(),
                    "keyword": query,
                }
            )
        return pd.DataFrame(rows)
    except Exception as exc:
        return pd.DataFrame([{"title": f"抓取失敗：{exc}", "link": "", "pubDate": "", "source": "", "keyword": query}])


@st.cache_data(ttl=60 * 60)
def fetch_website_title(url: str) -> str:
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = resp.text
        start = text.lower().find("<title>")
        end = text.lower().find("</title>")
        if start != -1 and end != -1 and end > start:
            return text[start + 7:end].strip().replace("\n", " ")
        return "（找不到標題）"
    except Exception as exc:
        return f"（抓取失敗：{exc}）"


def load_csv(uploaded, default_csv: str) -> pd.DataFrame:
    if uploaded is not None:
        return pd.read_csv(uploaded)
    return pd.read_csv(io.StringIO(default_csv))


def make_briefing(news_frames: dict[str, pd.DataFrame], top_clicks: pd.DataFrame, top_interactions: pd.DataFrame, top_products: pd.DataFrame) -> str:
    lines = [f"### 每日重點（{dt.date.today().isoformat()}）"]

    for region, frame in news_frames.items():
        if frame.empty:
            continue
        top_title = frame.iloc[0].get("title", "無資料")
        lines.append(f"- **{region}**：{top_title}")

    if not top_clicks.empty:
        r = top_clicks.iloc[0]
        lines.append(f"- **最高點擊貼文**：{r['competitor']} / {r['product']} / 點擊 {int(r['clicks'])}")

    if not top_interactions.empty:
        r = top_interactions.iloc[0]
        lines.append(
            f"- **最高互動貼文**：{r['competitor']} / 互動 {int(r['engagement'])}（讚{int(r['likes'])}+留言{int(r['comments'])}+分享{int(r['shares'])}）"
        )

    if not top_products.empty:
        hot = ", ".join([f"{x.product}（互動{int(x.engagement)}）" for x in top_products.itertuples(index=False)])
        lines.append(f"- **近期受歡迎新品/品類**：{hot}")

    return "\n".join(lines)


st.title("💎 每日水晶戰情室看板")
st.caption("資料來源：Google News RSS + 你上傳的社群/官網活動資料。預設資料僅示範，請替換為真實友商名單與貼文數據。")

with st.sidebar:
    st.header("看板設定")
    keywords_global = st.text_input("全球趨勢關鍵字", value="crystal market OR healing crystal trend")
    keywords_tw = st.text_input("台灣關鍵字", value="台灣 水晶 市場 OR 能量石")
    keywords_cn = st.text_input("大陸關鍵字", value="大陆 水晶 行业 OR 水晶 电商")
    keywords_hk = st.text_input("香港關鍵字", value="香港 水晶 市場")
    st.markdown("---")
    st.write("台灣頭部 20 友商（可編輯）")
    competitors_text = st.text_area("每行一個名稱", value="\n".join(TW_TOP20_DEFAULT), height=260)

competitor_names = [x.strip() for x in competitors_text.splitlines() if x.strip()]

news_topics = {
    "全球水晶趨勢": NewsTopic("全球水晶趨勢", keywords_global),
    "台灣產業動態": NewsTopic("台灣產業動態", keywords_tw),
    "大陸產業動態": NewsTopic("大陸產業動態", keywords_cn),
    "香港產業動態": NewsTopic("香港產業動態", keywords_hk),
}

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("1) 新聞與趨勢雷達")
    news_frames: dict[str, pd.DataFrame] = {}
    for region, topic in news_topics.items():
        df_news = fetch_google_news(topic.query)
        news_frames[region] = df_news
        with st.expander(region, expanded=False):
            for row in df_news.head(8).itertuples(index=False):
                title = getattr(row, "title", "")
                link = getattr(row, "link", "")
                pub = getattr(row, "pubDate", "")
                source = getattr(row, "source", "")
                if link:
                    st.markdown(f"- [{title}]({link})  ")
                else:
                    st.markdown(f"- {title}  ")
                st.caption(f"{source} | {pub}")

with col2:
    st.subheader("2) 台灣友商監控（Top 20）")
    st.write("目前追蹤名單", len(competitor_names), "家")
    st.dataframe(pd.DataFrame({"competitor": competitor_names}), use_container_width=True, height=250)

    st.markdown("**友商官網 / IG URL 清單（可上傳 CSV）**")
    comp_file = st.file_uploader("上傳友商清單 CSV", type=["csv"], key="comp")
    comp_df = load_csv(comp_file, DEFAULT_COMPETITOR_CSV)
    st.dataframe(comp_df, use_container_width=True, height=220)

    if st.button("抓取官網首頁標題（快速偵測是否有新活動頁）"):
        titles = []
        for row in comp_df.itertuples(index=False):
            website = getattr(row, "website", "")
            titles.append(fetch_website_title(website) if isinstance(website, str) and website else "")
        comp_df = comp_df.copy()
        comp_df["homepage_title"] = titles
        st.dataframe(comp_df, use_container_width=True, height=260)

st.markdown("---")
st.subheader("3) 社群貼文/活動成效分析（IG、官網、FB 皆可）")
st.caption("請上傳你每天匯出的貼文資料（至少要有 likes/comments/shares/clicks 欄位），即可算出點擊最高與互動最高貼文。")

post_file = st.file_uploader("上傳貼文資料 CSV", type=["csv"], key="post")
posts = load_csv(post_file, DEFAULT_POST_CSV)
required_cols = {"date", "competitor", "platform", "post_text", "product", "likes", "comments", "shares", "clicks"}

if not required_cols.issubset(set(posts.columns)):
    st.error(f"欄位不足，必須包含：{sorted(required_cols)}")
else:
    for c in ["likes", "comments", "shares", "clicks"]:
        posts[c] = pd.to_numeric(posts[c], errors="coerce").fillna(0)
    posts["engagement"] = posts["likes"] + posts["comments"] + posts["shares"]

    left, right = st.columns(2)
    with left:
        st.markdown("**點擊最高貼文 Top 10**")
        top_clicks = posts.sort_values("clicks", ascending=False).head(10)
        st.dataframe(top_clicks[["date", "competitor", "platform", "product", "clicks", "post_text"]], use_container_width=True)

        st.markdown("**互動最高貼文 Top 10**")
        top_interactions = posts.sort_values("engagement", ascending=False).head(10)
        st.dataframe(
            top_interactions[["date", "competitor", "platform", "product", "engagement", "likes", "comments", "shares", "post_text"]],
            use_container_width=True,
        )

    with right:
        st.markdown("**熱門產品 / 新品（以互動總量排序）**")
        top_products = posts.groupby("product", as_index=False)[["engagement", "clicks"]].sum().sort_values("engagement", ascending=False).head(10)
        st.dataframe(top_products, use_container_width=True)

        st.markdown("**友商整體表現排行（可看誰最近操作最強）**")
        rank_df = (
            posts.groupby("competitor", as_index=False)[["engagement", "clicks"]]
            .sum()
            .sort_values(["engagement", "clicks"], ascending=False)
        )
        st.dataframe(rank_df, use_container_width=True)

    st.markdown("---")
    st.subheader("4) 自動產生今日戰情報告")
    briefing = make_briefing(news_frames, top_clicks, top_interactions, top_products.head(5))
    st.markdown(briefing)
    st.download_button("下載今日戰情摘要（Markdown）", data=briefing, file_name=f"crystal_briefing_{dt.date.today().isoformat()}.md")

with st.expander("建議你接下來可擴充（進階）"):
    st.markdown(
        textwrap.dedent(
            """
            1. 串接官方 API：Meta Graph API（IG/Facebook）、Google Analytics、Search Console。
            2. 每天定時爬資料：用 GitHub Actions / Airflow 在固定時間匯入 CSV。
            3. 加上 NLP 分析：自動分類貼文主題（招財、療癒、愛情、人際、職場）。
            4. 做預警規則：友商某篇互動暴增 > 2x 時，推播到 Slack/LINE。
            """
        )
    )
