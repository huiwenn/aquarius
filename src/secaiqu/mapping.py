"""
Province → 色彩区 (stylistic color region) mapping for Chinese folk music.

The system includes 11 Han Chinese stylistic regions (色彩区) based on
geographic, linguistic, and musical characteristics, plus 4 minority/border
regions (少数民族民歌区) representing non-Han musical traditions.

Reference: 江明惇《汉族民歌概论》; 周青青《中国民间音乐概论》
"""

import pandas as pd

# ─────────────────────────────────────────────────────────────
# Province → 色彩区 mapping
# ─────────────────────────────────────────────────────────────
# Keys are the exact province strings from master_table.parquet.
# Ambiguous provinces are mapped to their DOMINANT region with a comment.

PROVINCE_TO_SECAIQU: dict[str, str | None] = {
    # ── 东北部平原 ──
    # 山东、河北、辽吉黑大部及豫东南、苏北徐州一带
    "Shandong": "东北部平原",
    "Hebei": "东北部平原",
    "Liaoning": "东北部平原",
    "Jilin": "东北部平原",
    "Heilongjiang": "东北部平原",
    "Tianjin": "东北部平原",
    "Beijing": "东北部平原",  # geographically in 东北部平原 zone
    "Northeastern": "东北部平原",  # generic label, maps here

    # ── 西北部高原 ──
    # 山西、甘肃、宁夏大部、陕北、关中、青海东部及内蒙古西部
    "Shanxi": "西北部高原",
    "Gansu": "西北部高原",
    "Ningxia": "西北部高原",
    "Shaanxi": "西北部高原",  # ambiguous: 关中 is 西北, southern Shaanxi could be 西南
    "Northern Shaanxi": "西北部高原",  # 陕北 — core 西北 (信天游 heartland)
    "Qinghai": "西北部高原",
    "Inner Mongolia": "西北部高原",  # ambiguous: western part is 西北, eastern is closer to 东北

    # ── 江淮 ──
    # 苏北、皖北及豫东南部分地区
    "Anhui": "江淮",  # ambiguous: 皖北 is 江淮, 皖南东部 is 江浙平原; bulk of Anhui folk songs are 江淮

    # ── 江浙平原 ──
    # 苏南、皖南东部、上海及浙江大部
    "Jiangsu": "江浙平原",  # ambiguous: 苏北 is 江淮, 苏南 is 江浙; Anthology volumes are Jiangsu I & II without sub-region
    "Shanghai": "江浙平原",
    "Zhejiang": "江浙平原",
    "Jiangnan": "江浙平原",  # generic label for the Jiangnan region

    # ── 闽台 ──
    # 福建大部、台湾及广东潮汕部分县市
    "Fujian": "闽台",
    "Taiwan": "闽台",

    # ── 粤 ──
    # 广东大部（客家区、粤北少数民族区除外）、桂东南及海南汉族聚居地
    "Guangdong": "粤",  # ambiguous: Hakka areas → 客家特区, Chaoshan → 闽台; default to 粤 as dominant
    "Hainan": "粤",
    "Guangxi": "粤",  # ambiguous: 桂东南 is 粤, rest has Zhuang/minority music; default 粤

    # ── 江汉 ──
    # 湖北大部及豫南、豫西南、湘北部分地区
    "Hubei": "江汉",
    "Henan": "江汉",  # ambiguous: 豫东南 is 江淮/东北部平原, 豫南豫西南 is 江汉; Henan straddles 3 regions

    # ── 湘 ──
    "Hunan": "湘",  # ambiguous: 湘北 overlaps 江汉, but core Hunan is 湘

    # ── 赣 ──
    "Jiangxi": "赣",

    # ── 西南高原 ──
    # 巫山以西、秦岭以南、横断山以东
    "Sichuan": "西南高原",
    "Sichuan/Chongqing": "西南高原",
    "Guizhou": "西南高原",
    "Yunnan": "西南高原",  # ambiguous: 无量山以南 has minority music outside the system

    # ── 客家特区 ──
    "Guangdong (Hakka Music), Northern Shaanxi": "客家特区",  # explicitly tagged Hakka

    # ── 北方草原文化民歌区 (少数民族) ──
    # Inner Mongolia is ambiguous: western part is Han (西北部高原), eastern/grassland is Mongolian
    # Mapped to 西北部高原 above for default; items tagged as Mongolian style should override

    # ── 新疆民歌区 (少数民族) ──
    "Xinjiang": "新疆民歌区",  # Uyghur, Kazakh, Kyrgyz — Islamic-influenced musical systems

    # ── Invalid data ──
    "/": None,
}


# ─────────────────────────────────────────────────────────────
# 色彩区 metadata
# ─────────────────────────────────────────────────────────────

SECAIQU_METADATA: dict[str, dict] = {
    "东北部平原": {
        "name_en": "Northeastern Plains",
        "geography": "山东、河北、辽吉黑大部及豫东南、苏北徐州一带",
        "representative_genres": "小调最突出，次为秧歌、号子，山歌很少",
        "representative_songs": ["小白菜", "放风筝", "沂蒙山小调", "绣荷包"],
        "style": "六、七声音阶为主；徵调式为主，商、宫、羽次之；多四句体",
    },
    "西北部高原": {
        "name_en": "Northwestern Plateau",
        "geography": "山西、甘肃、宁夏大部、陕北、关中、青海东部及内蒙古西部",
        "representative_genres": "山歌最突出（信天游、山曲、爬山调、花儿）",
        "representative_songs": ["走西口", "兰花花", "想亲亲", "脚夫调"],
        "style": "多种五声/燕乐七声音阶；徵、商调式为主",
    },
    "江淮": {
        "name_en": "Jianghuai",
        "geography": "苏北、皖北及豫东南部分地区",
        "representative_genres": "小调、山歌、渔歌",
        "representative_songs": ["凤阳花鼓", "拔根芦柴花", "慢赶牛"],
        "style": "由六、七声音阶向五声音阶过渡；宫、徵调式为主",
    },
    "江浙平原": {
        "name_en": "Jiangzhe Plains",
        "geography": "苏南、皖南东部、上海及浙江大部",
        "representative_genres": "小调、山歌、渔歌",
        "representative_songs": ["茉莉花", "孟姜女", "无锡景", "紫竹调"],
        "style": "五声音阶为主；五声徵调式最多，宫、羽次之",
    },
    "闽台": {
        "name_en": "Fujian-Taiwan",
        "geography": "福建大部、台湾及广东潮汕部分县市",
        "representative_genres": "号子、山歌、茶歌、锁歌、龙船歌、小调",
        "representative_songs": ["长工歌", "砍柴山歌", "锁歌"],
        "style": "以二—三度或双三度音列为基础；羽、徵调式为主",
    },
    "粤": {
        "name_en": "Guangdong",
        "geography": "广东大部（客家区、粤北少数民族区除外）、桂东南及海南汉族聚居地",
        "representative_genres": "山歌、号子、渔歌",
        "representative_songs": ["哩哩美", "咸水歌", "调声", "对花"],
        "style": "五声羽、徵、商调式及六声徵调式；两句体、四句体",
    },
    "江汉": {
        "name_en": "Jianghan",
        "geography": "湖北大部及豫南、豫西南、湘北部分地区",
        "representative_genres": "田歌、小调、号子、山歌",
        "representative_songs": ["催咚催", "喇叭调", "桐柏山歌"],
        "style": "三声腔及四、五声音阶音调；有赶五句、穿号子等结构",
    },
    "湘": {
        "name_en": "Hunan",
        "geography": "基本以湖南本土为限",
        "representative_genres": "山歌、田歌、号子、小调",
        "representative_songs": ["上四川", "看郎", "送表妹"],
        "style": "湘羽音调体系",
    },
    "赣": {
        "name_en": "Jiangxi",
        "geography": "赣中、赣北、赣东",
        "representative_genres": "山歌、田歌、茶歌、小调、号子",
        "representative_songs": ["杜鹃花开", "青草小河边"],
        "style": "五声音阶为主；徵调式居多，羽调式次之",
    },
    "西南高原": {
        "name_en": "Southwestern Plateau",
        "geography": "巫山以西、秦岭与岷山以南、横断山以东、无量山与哀牢山以北的汉族地区",
        "representative_genres": "山歌、小调、号子",
        "representative_songs": ["槐花几时开", "小河淌水", "采花", "放马山歌"],
        "style": "四、五声羽、徵、商调式为基础",
    },
    "客家特区": {
        "name_en": "Hakka Special Zone",
        "geography": "粤、闽、赣、湘、桂、台等省区的客家人聚居地",
        "representative_genres": "山歌",
        "representative_songs": ["送人离别水东西", "风吹竹叶"],
        "style": "四声羽调式与五声徵调式为主",
    },
    # ── 少数民族民歌区 (4 minority folk song regions) ──
    "北方草原文化民歌区": {
        "name_en": "Northern Grassland Culture",
        "geography": "内蒙古草原、东北部分地区（蒙古族聚居区）",
        "representative_genres": "长调（乌日汀道）、短调、呼麦、酒歌、赞歌",
        "representative_songs": ["辽阔的草原", "牧歌", "嘎达梅林", "森吉德玛"],
        "style": "宽广悠长的旋律线；羽调式和宫调式为主；自由节拍长调与规整节拍短调并存",
        "minority": True,
    },
    "新疆民歌区": {
        "name_en": "Xinjiang (Islamic-influenced)",
        "geography": "新疆维吾尔自治区（维吾尔族、哈萨克族、柯尔克孜族等聚居区）",
        "representative_genres": "木卡姆、赛乃姆、麦西来甫、冬不拉弹唱",
        "representative_songs": ["阿拉木汗", "达坂城的姑娘", "掀起你的盖头来", "半个月亮爬上来"],
        "style": "阿拉伯-波斯音乐体系影响；多用增二度音程；七声音阶为主；节奏型丰富",
        "minority": True,
    },
    "藏族民歌区": {
        "name_en": "Tibetan (Buddhist-influenced)",
        "geography": "西藏、青海藏区、四川甘孜阿坝、甘肃甘南、云南迪庆",
        "representative_genres": "山歌（拉伊）、酒歌（昌鲁）、弦子、锅庄、囊玛",
        "representative_songs": ["北京的金山上", "逛新城", "在那东山顶上"],
        "style": "五声音阶为主；la-do-re或do-re-mi三音列核心；大跳音程常见；高亢开阔",
        "minority": True,
    },
    "西南多民族古老原始文化民歌区": {
        "name_en": "Southwestern Multi-ethnic Ancient Culture",
        "geography": "云南南部、贵州西南、广西西北（苗、彝、侗、壮、瑶、白、纳西、哈尼等民族聚居区）",
        "representative_genres": "大歌（侗族）、飞歌（苗族）、对歌、情歌、丧歌",
        "representative_songs": ["侗族大歌", "苗族飞歌", "阿诗玛"],
        "style": "多声部民歌（侗族大歌）；原始古朴音调；三音列、四音列多见；与自然音响密切相关",
        "minority": True,
    },
}

# Provinces that straddle multiple 色彩区 — documented for downstream disambiguation
AMBIGUOUS_PROVINCES: dict[str, list[str]] = {
    "Jiangsu": ["江浙平原", "江淮"],
    "Anhui": ["江淮", "江浙平原"],
    "Henan": ["东北部平原", "江淮", "江汉"],
    "Guangdong": ["粤", "闽台", "客家特区"],
    "Inner Mongolia": ["西北部高原", "东北部平原", "北方草原文化民歌区"],  # Han west vs Han east vs Mongolian grassland
    "Shaanxi": ["西北部高原", "西南高原"],
    "Hunan": ["湘", "江汉"],
    "Guangxi": ["粤", "西南多民族古老原始文化民歌区"],  # 桂东南 Han vs 桂西北 minority
    "Yunnan": ["西南高原", "西南多民族古老原始文化民歌区", "藏族民歌区"],  # Han vs minority vs 迪庆藏区
    "Guizhou": ["西南高原", "西南多民族古老原始文化民歌区"],  # Han vs 苗/侗/彝
    "Qinghai": ["西北部高原", "藏族民歌区"],  # Han east vs Tibetan west
    "Sichuan": ["西南高原", "藏族民歌区"],    # Basin Han vs 甘孜阿坝 Tibetan
}


def assign_secaiqu(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'secaiqu' column based on province → 色彩区 mapping.

    Items with no province or provinces not in the mapping get NaN.
    """
    df = df.copy()
    df["secaiqu"] = df["province"].map(PROVINCE_TO_SECAIQU)
    return df
