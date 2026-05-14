import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="粽子销售看板", layout="wide")

# ====================== 路径 ======================
excel_path = "粽子销售数据.xlsx"

# ====================== 读取数据 ======================
try:
    # 1. 销售排行数据
    df_latest = pd.read_excel(
        excel_path, sheet_name="最新数据", header=None, skiprows=3, nrows=23,
        usecols=[0,1,2,4,6,8],
        names=["酒店名称","25年销售额","26年销售额","同比增减%","目标完成率","去年完成率"]
    )
    
    # 2. 阶段对比数据（包含合计行）
    df_pickup = pd.read_excel(
        excel_path, sheet_name="粽子销售PICKUP", header=None, skiprows=3, nrows=23,
        names=["酒店名称", "节前38天_25年", "节前38天_26年", "节前26天_25年", "节前26天_26年",
               "节前19天_25年", "节前19天_26年", "节前9天_25年", "节前9天_26年", "累计收入_25年", "累计收入_26年"]
    )
except Exception as e:
    st.error(f"❌ 读取失败：请确认文件 `{excel_path}` 存在。错误详情：{e}")
    st.stop()

# ====================== 清洗 ======================
def num(x):
    if pd.isna(x) or str(x).strip() in ["-", "nan"]:
        return 0.0
    try:
        return float(str(x).replace(",","").strip())
    except:
        return 0.0

# 清洗排行数据
df_latest = df_latest.dropna(subset=["酒店名称"])
df_latest["25年销售额"] = df_latest["25年销售额"].apply(num)
df_latest["26年销售额"] = df_latest["26年销售额"].apply(num)
df_latest["同比增减%"] = df_latest["同比增减%"].apply(num) * 100
df_latest["目标完成率"] = df_latest["目标完成率"].apply(num) * 100
df_latest["去年完成率"] = df_latest["去年完成率"].apply(num) * 100

# 分离酒店和合计（合计行强制不参与排序）
df_hotel = df_latest[~df_latest["酒店名称"].str.contains("合计", na=False)].copy()
df_total = df_latest[df_latest["酒店名称"].str.contains("合计", na=False)].copy()

# 清洗阶段对比数据
for col in df_pickup.columns:
    if col != "酒店名称":
        df_pickup[col] = df_pickup[col].apply(num)

# ====================== 增长率函数（26年为0则不显示） ======================
def growth(v25, v26):
    if v26 == 0:
        return None, None  # 26年=0，直接不显示百分比
    if v25 == 0:
        return "—", "#888"
    r = (v26 - v25)/v25 * 100
    if r > 0:
        return f"⬆️ {r:.1f}%", "red"
    elif r < 0:
        return f"⬇️ {abs(r):.1f}%", "green"
    else:
        return "➡️ 0.0%", "gray"

# ====================== 页面 ======================
st.title("🍙 粽子销售看板")
st.divider()

# ---------------------- 1. 酒店粽子销售排行 ----------------------
st.subheader("🏆 酒店粽子销售排行")

cs1, cs2 = st.columns([2,3])
with cs1:
    sort_col = st.selectbox("排序字段",["26年销售额","同比增减%","目标完成率","去年完成率"], index=0)
with cs2:
    order = st.radio("排序方式",["降序","升序"], horizontal=True, index=0)

asc = True if order=="升序" else False
df_hotel_sorted = df_hotel.sort_values(by=sort_col, ascending=asc).reset_index(drop=True)
df_sort = pd.concat([df_hotel_sorted, df_total], ignore_index=True)

# ====================== 表格 + 图表 ======================
ct, cc = st.columns([0.9, 2.1])

with ct:
    show = df_sort.copy()
    show["26年销售额"] = show["26年销售额"].apply(lambda x: f"{x/10000:.2f}万")
    show["同比增减%"] = show["同比增减%"].apply(lambda x: f"{x:.1f}%")
    show["目标完成率"] = show["目标完成率"].apply(lambda x: f"{x:.1f}%")
    show["去年完成率"] = show["去年完成率"].apply(lambda x: f"{x:.1f}%")
    show = show[["酒店名称","26年销售额","同比增减%","目标完成率","去年完成率"]]

    st.dataframe(
        show,
        hide_index=True,
        height=580,
        use_container_width=True,
        column_config={
            "酒店名称": st.column_config.TextColumn("酒店名称", width="small"),
            "26年销售额": st.column_config.TextColumn("26年销售额", width="small"),
            "同比增减%": st.column_config.TextColumn("同比增减%", width="small"),
            "目标完成率": st.column_config.TextColumn("目标完成率", width="small"),
            "去年完成率": st.column_config.TextColumn("去年完成率", width="small"),
        }
    )

with cc:
    dc = df_sort[~df_sort["酒店名称"].str.contains("合计", na=False)]
    fig = go.Figure()
    
    fig.add_bar(x=dc["酒店名称"], y=dc["25年销售额"]/10000, name="25年销售额", marker_color="#1f77b4", yaxis="y1")
    fig.add_bar(x=dc["酒店名称"], y=dc["26年销售额"]/10000, name="26年销售额", marker_color="#ff7f0e", yaxis="y1")
    fig.add_scatter(x=dc["酒店名称"], y=dc["同比增减%"], name="同比增减%", line=dict(color="red",width=3), mode="lines+markers", yaxis="y2")
    fig.add_scatter(x=dc["酒店名称"], y=dc["目标完成率"], name="目标完成率", line=dict(color="blue",width=3), mode="lines+markers", yaxis="y2", visible="legendonly")
    fig.add_scatter(x=dc["酒店名称"], y=dc["去年完成率"], name="去年完成率", line=dict(color="green",width=3), mode="lines+markers", yaxis="y2", visible="legendonly")

    fig.update_layout(
        height=600, 
        xaxis_tickangle=-45, 
        barmode="group",
        yaxis=dict(title="万元"),
        yaxis2=dict(title="%", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.05, title=None),
        title_text=""
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------- 2. 单酒店各阶段对比（默认选中：合计） ----------------------
st.subheader("📈 单酒店各阶段对比")
col1, col2 = st.columns([1,5])

with col1:
    hotel_list = df_pickup["酒店名称"].dropna().unique().tolist()
    # 默认选中 合计
    sel = st.selectbox("选择酒店", hotel_list, index=hotel_list.index("合计"))

with col2:
    stages = ["节前38天","节前26天","节前19天","节前9天","累计收入"]
    
    match = df_pickup[df_pickup["酒店名称"] == sel]
    if match.empty:
        st.warning("未找到数据")
        st.stop()
    row = match.iloc[0]

    y25 = [
        row["节前38天_25年"],
        row["节前26天_25年"],
        row["节前19天_25年"],
        row["节前9天_25年"],
        row["累计收入_25年"]
    ]
    y26 = [
        row["节前38天_26年"],
        row["节前26天_26年"],
        row["节前19天_26年"],
        row["节前9天_26年"],
        row["累计收入_26年"]
    ]

    w25 = [round(v/10000,2) for v in y25]
    w26 = [round(v/10000,2) for v in y26]

    fig = go.Figure()
    fig.add_bar(x=stages, y=w25, name="2025", marker_color="#1f77b4", textposition="outside", text=[f"{x}万" for x in w25])
    fig.add_bar(x=stages, y=w26, name="2026", marker_color="#ff7f0e", textposition="outside", text=[f"{x}万" for x in w26])

    for i,(a,b) in enumerate(zip(y25,y26)):
        txt, color = growth(a, b)
        if txt is None:  # 26年=0，不显示
            continue
        
        # ✅ 关键改动：用 yref="paper" 让标签位置和柱子高度无关，固定在图表上方
        fig.add_annotation(
            x=i, 
            y=0.95,  # 固定在图表高度的95%位置，永远在柱子上方
            yref="paper",  # 使用相对位置，和数值轴无关
            text=txt, 
            font=dict(size=13, color=color),
            showarrow=False, 
            xanchor="center"
        )

    fig.update_layout(
        height=500, 
        barmode="group", 
        margin=dict(t=100, b=20)  # 顶部留足空间放标签
    )
    st.plotly_chart(fig, use_container_width=True)