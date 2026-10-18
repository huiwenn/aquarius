"""
Build data/contrast/candidates_clean/创作民歌.json: contrast set of COMPOSED folk-style songs (创作民歌).

Every video ID below was returned by live searches with src/secaiqu/v2/search.py
(AQ_COLLECTION=data/contrast, log: data/contrast/logs/search_bili.jsonl). This script re-reads that log
for title / channel / duration / first query, and refuses any ID that is not in the log or is outside 60-600 s.
Authorship (composer, lyricist, year) comes from the cited sources. Where a source gives no lyricist,
lyricist is null. `knowledge` = no source checked in this task.

Rank order = list order; entries with note starting "backup" come last.
Run (py312):  python src/contrast/build_chuangzuo.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data/contrast/logs/search_bili.jsonl"
OUT = ROOT / "data/contrast/candidates_clean/创作民歌.json"

HY = "https://herongyang.com/Chinese/Music/"
CP100 = "https://zh.wikipedia.org/wiki/中宣部推荐100首爱国歌曲"
ZW = "https://zh.wikipedia.org/wiki/"

# (song_name, bvid, composer, lyricist, year, year_kind, idiom_region, singer, performance_type, sources, note)
E = [
 ("南泥湾", "BV1NU4y1X7hd", "马可", "贺敬之", 1943, "composition", "西北部高原 (陕北)", "郭兰英", "canonical_cover",
  [ZW + "南泥灣_(歌曲)", CP100], "first sung by 王昆 (Wikipedia); 郭兰英 version of 1964 Dongfanghong epic"),
 ("我的祖国", "BV1Zc411P7Dv", "刘炽", "乔羽", 1956, "composition", "全国 (民歌风，无特定地区)", "郭兰英", "original",
  [HY + "1956-Wo-De-Zu-Guo.html", CP100], "film 上甘岭 (1956) lead vocal 郭兰英"),
 ("红梅赞", "BV1cw411i7Nz", "羊鸣、姜春阳、金砂", "阎肃", 1964, "composition", "西南 (四川民歌风)", "万馥香", "original",
  [HY + "1964-Hong-Mei-Zan.html", CP100], "opera 江姐; 1965 recording by first singer per uploader; HY lists only 羊鸣, CP100 lists the trio"),
 ("唱支山歌给党听", "BV1LX4y1w7Lg", "朱践耳", "蕉萍 (姚筱舟)", 1963, "composition", "藏族 (演唱风格; 曲调为新民歌)", "才旦卓玛", "original",
  [ZW + "唱支山歌给党听", CP100], "poem 1958 by 蕉萍, set to music 1963 after Lei Feng diary; made famous by 才旦卓玛"),
 ("在希望的田野上", "BV1ha9hBgE38", "施光南", "晓光 (陈晓光)", 1981, "composition", "全国 (农村题材民歌风)", "彭丽媛", "original",
  [ZW + "在希望的田野上", CP100], "CP100 dates 1981; Wikipedia says handed to 彭丽媛 in 1982; clip is only 64 s"),
 ("祝酒歌", "BV1Q44y147d1", "施光南", "韩伟", 1979, "composition", "全国 (民歌风)", "李光羲", "original",
  [ZW + "施光南"], "year from Wikipedia (施光南); lyricist 韩伟 from knowledge, not checked"),
 ("月光下的凤尾竹", "BV19Y4y1D7ni", "施光南", "倪维德", 1979, "composition", "西南多民族 (傣族)", "于淑珍", "canonical_cover",
  ["https://m.thepaper.cn/baijiahao_16754999", "https://www.sohu.com/a/289475348_155679"], "written in Dehong 1979 (web search result)"),
 ("吐鲁番的葡萄熟了", "BV124411n7qZ", "施光南", "清波", 1980, "composition", "新疆 (维吾尔族)", "关牧村", "canonical_cover",
  [ZW + "施光南"], "year from Wikipedia (施光南); lyricist 清波 from knowledge, not checked"),
 ("敖包相会", "BV1Ao4y1F7Cb", "通福", "玛拉沁夫", 1953, "composition", "北方草原 (蒙古族)", "耿莲凤、张振富", "original",
  [HY + "1953-Ao-Bao-XIang-Hui.html"], "film 草原上的人们; tune reworked from a Hailar love song (HY and web search)"),
 ("草原上升起不落的太阳", "BV1P7411e75b", "美丽其格", "美丽其格", 1951, "composition", "北方草原 (蒙古族)", "德德玛", "later_cover",
  [HY + "1951-Cao-Yuan-Shang-Sheng-Qi-Bu-Luo-De-Tai-Yang.html", CP100], "HY 1951, CP100 and a web search 1952 (student work, Central Conservatory)"),
 ("美丽的草原我的家", "BV19N4y127sr", "阿拉腾奥勒", "火华", 1978, "composition", "北方草原 (蒙古族)", "德德玛", "original",
  [HY + "1976-Mei-Li-De-Cao-Yuan-Wo-De-Jia.html", CP100], "web search gives 1978 (first sung at Guangzhou fair); HY gives 1976; CP100 '1970s'"),
 ("草原之夜", "BV1jn4y1d7sn", "田歌", "张加毅", 1959, "composition", "新疆 (哈萨克/北疆草原)", "孟贵彬", "original",
  [HY + "1959-Cao-Yuan-Zhi-Ye.html"], "1959 original recording by 孟贵彬"),
 ("翻身农奴把歌唱", "BV1mh411U7iY", "阎飞", "李堃", 1965, "first_publication", "藏族", "才旦卓玛", "original",
  [ZW + "翻身农奴把歌唱", CP100], "theme of documentary 今日西藏 (1965); sources conflict on composition year (1954 CP100, 1959 web search)"),
 ("洗衣歌", "BV1MK4y1R7HN", "罗念一", "李俊琛", 1964, "composition", "藏族", "才旦卓玛", "canonical_cover",
  ["https://chinadigitaltimes.net/2011/06/laundry-song-a-tibetan-red-song/", "https://www.163.com/dy/article/E2VCB8J60528BRQQ.html"], "web search credits 罗念一 (music) and 李俊琛 (lyrics), 1964"),
 ("歌唱二郎山", "BV1ur421A7qw", "时乐濛", "洛水", 1950, "composition", "藏族 (川藏公路)", "孟贵彬", "original",
  ["knowledge", "bilibili title of BV1ur421A7qw: 洛水 词; 时乐濛 曲"], "year 1950 from knowledge only, not checked; credits also in uploader title"),
 ("北风吹", "BV1qW4y1o7DQ", "马可、张鲁、瞿维 等 (延安鲁艺集体)", "贺敬之、丁毅", 1945, "composition", "西北部高原 (河北民歌曲调素材)", "王昆", "original",
  [HY + "1945-Bei-Feng-Chui.html", "web search: opera 白毛女 collective of 鲁艺, 马可 张鲁 瞿维 etc."], "opera 白毛女 aria; HY lists 马可 / 贺敬之 only"),
 ("咱们工人有力量", "BV1Rw41187UR", "马可", "马可", 1948, "composition", "东北部平原 (东北秧歌调与号子)", None, "later_cover",
  [ZW + "咱们工人有力量", CP100], "Wikipedia: 马可词曲, 1948; CP100 says 1947; singer not named by uploader"),
 ("延安颂", "BV1Xx421Q71u", "郑律成", "莫耶", 1938, "composition", "西北部高原 (延安)", "郑律成", "original",
  [ZW + "延安颂_(消歧义)", CP100], "uploader says film 永不消逝的电波 (1958) version sung by the composer"),
 ("二月里来", "BV1XXUGBLEjx", "冼星海", "塞克", 1939, "composition", "西北部高原 (陕北; 旋律带江南风味)", "周小燕", "canonical_cover",
  [ZW + "二月里来", CP100], "from 生产大合唱; 1953 recording per uploader"),
 ("黄河船夫曲", "BV1jE411y7gA", "冼星海", "光未然", 1939, "composition", "西北部高原 (晋陕黄河船夫号子)", "王宏伟", "later_cover",
  [ZW + "黄河大合唱", CP100], "movement 1 of the Yellow River Cantata; modern solo performance"),
 ("松花江上", "BV1FU4y1N7VU", "张寒晖", "张寒晖", 1936, "composition", "东北部平原", None, "later_cover",
  [HY + "1936-Song-Hua-Jiang-Shang.html", CP100], "uploader dates it 1935; HY 1936; singer not named"),
 ("浏阳河", "BV1oK4y157es", "朱立奇、唐璧光", "徐叔华", 1951, "composition", "湘 (湖南)", "李谷一", "canonical_cover",
  [HY + "1951-Liu-Yang-He.html"], "song already in corpus as other recordings; this is a canonical recording"),
 ("十送红军", "BV1445nzxEaj", "朱正本 (编曲)", "张士燮", 1962, "composition", "赣 (江西民歌风)", None, "canonical_cover",
  [CP100], "song already in corpus as other recordings; uploader: 1963 version; CP100: 朱正本 编曲, Jiangxi folk style"),
 ("映山红", "BV1rt411T71u", "傅庚辰", "陆柱国", 1974, "composition", "赣 (江西)", "邓玉华", "original",
  [CP100], "film 闪闪的红星 version; song already in corpus as another recording"),
 ("洞庭鱼米乡", "BV1cV4y1s7Gd", "白诚仁", "叶蔚林", 1964, "composition", "湘 (湖南)", "何纪光", "original",
  [HY + "1964-Dong-Ting-Yu-Mi-Xiang.html"], "1964 recording by 何纪光"),
 ("小背篓", "BV1kx411m7C8", "白诚仁", "欧阳常林", 1990, "composition", "湘 (湖南)", "宋祖英", "original",
  [ZW + "小背篓_(宋祖英歌曲)"], "1990 CCTV Spring Festival Gala"),
 ("山歌好比春江水", "BV1NZ421M7MS", "雷振邦", "乔羽", 1960, "composition", "西南 (广西壮族)", "傅锦华", "original",
  [HY + "1960-Shan-Ge-Hao-Bi-Chun-Jiang-Shui.html"], "1960 recording per uploader; Liu Sanjie"),
 ("蝴蝶泉边", "BV1pt41167Ym", "雷振邦", "季康", 1959, "composition", "西南多民族 (云南白族)", "电影原声 (赵履珠、李世荣, 见同类上传标题)", "original",
  [HY + "1959-Hu-Die-Quan-Bian.html"], "built from two Bai folk songs (HY); film 五朵金花"),
 ("婚誓", "BV1w84y1e7Gk", "雷振邦", "于彦夫", 1957, "composition", "西南多民族 (云南)", "吴影、温明兰", "original",
  [HY + "1957-Hun-Shi.html"], "film 芦笙恋歌 (1957)"),
 ("马铃儿响来玉鸟儿唱", "BV1uE411f7fU", "罗宗贤、葛炎", "葛炎、刘琼", 1964, "composition", "西南多民族 (云南彝族, 阿诗玛)", "胡松华、杜丽华", "original",
  [HY + "1964-Ma-Ling-Er-Xiang-Lai-Yu-Niao-Er-Chang.html"], "film 阿诗玛 (1964)"),
 ("阿佤人民唱新歌", "BV11p4y1B79J", "杨正仁", "杨正仁", 1964, "composition", "西南多民族 (云南佤族)", None, "later_cover",
  ["https://www.toutiao.com/zixun/7500362759855589414/", "https://www.rmzxw.com.cn/c/2020-01-22/2511782.shtml"], "web search: soldier 杨正仁 wrote words and music 1964 on Wa folk material; 1972 recording per uploader"),
 ("边疆的泉水清又纯", "BV1fx411g7Z1", "王酩", "凯传", 1977, "composition", "西南多民族 (云南边疆)", "李谷一", "original",
  [HY + "1977-Bian-Jiang-De-Quan-Shui-Qing-You-Chun.html", CP100], "film 黑三角 insert; CP100 says 1970s"),
 ("红太阳照边疆", "BV1ieCbYxEU4", "金凤浩", "韩允浩", 1966, "composition", "朝鲜族 (延边)", "卞英花", "canonical_cover",
  [ZW + "红太阳照边疆"], "Korean-style song written 1966 in Helong, Yanbian"),
 ("山丹丹开花红艳艳", "BV1wg411W7Ed", "关鹤岩", "关鹤岩", 1971, "composition", "西北部高原 (陕北/陇东)", "杨巧", "original",
  [HY + "1971-Shan-Dan-Dan-Hua-Kai-Hong-Yan-Yan.html"], "web search: built from a Shaanbei xintianyou and a Longdong tune, finished end of 1971; 1971 first recording"),
 ("弹起我心爱的土琵琶", "BV1Ly4y1q74v", "吕其明", "芦芒、何彬", 1956, "composition", "山东 (齐鲁)", None, "later_cover",
  [HY + "1956-Tan-Qi-Wo-Xin-Ai-De-Tu-Pi-Pa.html"], "film 铁道游击队 (1956); strong Shandong folk style (HY)"),
 ("九九艳阳天", "BV1rs4y177bp", "高如星", "胡石言", 1957, "composition", "江淮 (苏北柳堡)", "电影原声 (1958 版)", "original",
  [HY + "1957-Jiu-Jiu-Yan-Yang-Tian.html"], "HY prints the two names with the roles the other way round (lyrics 高如星, music 胡石言); roles here follow knowledge (高如星 also composed 汾河流水哗啦啦), please check"),
 ("采茶舞曲", "BV1fJ4m1Y7NU", "周大风", "周大风", 1958, "composition", "江浙平原 (浙江)", "越歌表演 (歌手未注明)", "later_cover",
  [HY + "1958-Cai-Cha-Wu-Qu.html"], "from Yue opera 雨前曲; first singer 叶彩华 (HY)"),
 ("太湖美", "BV1Sge4zFEzr", "龙飞", "任红举", 1978, "composition", "江浙平原 (太湖)", "李惠兰", "original",
  ["https://www.yzwb.net/news/jiangsu/wuxi/202508/t20250825_254617.html"], "web search: written 1978 by 任红举 and 龙飞; uploader: 1979 first version by 李惠兰"),
 ("沂蒙颂", "BV1yN9pYjEb8", "刘廷禹", "李承祥", 1974, "composition", "山东 (沂蒙)", "梦鸽", "original",
  [HY + "1974-Yi-Meng-Song.html"], "from the ballet film 沂蒙颂"),
 ("谁不说俺家乡好", "BV1Fp4y1X7Z6", "吕其明、杨庶正、肖培珩 (联合署名)", "吕其明、杨庶正、肖培珩 (联合署名)", 1961, "composition", "山东 (沂蒙)", "任桂珍", "original",
  [CP100, HY + "1961-Shui-Bu-Shuo-An-Jia-Xiang-Hao.html"], "film 红日; CP100 gives joint credit, HY gives roles; who wrote music vs lyrics unclear"),
 ("人说山西好风光", "BV124411979B", "张棣昌", "乔羽", 1959, "composition", "山西 (晋)", "郭兰英", "original",
  [HY + "1959-Ren-Shuo-Shan-Xi-Hao-Feng-Guang.html"], "film insert (uploader: film 我们村里的年轻人, 1963); HY dates the song 1959"),
 ("汾河流水哗啦啦", "BV1iV4y1k7R3", "高如星", "乔羽", 1963, "first_publication", "山西 (晋)", "王爱爱、孟贵彬", "original",
  ["https://www.last.fm/music/%E5%90%B4%E9%9B%81%E6%B3%BD/_/%E6%B1%BE%E6%B2%B3%E6%B5%81%E6%B0%B4%E5%93%97%E5%95%A6%E5%95%A6+(%E7%94%B5%E5%BD%B1%E3%80%8A%E6%B1%BE%E6%B0%B4%E9%95%BF%E6%B5%81%E3%80%8B%E4%B8%BB%E9%A2%98%E6%AD%8C)/+wiki", "bilibili title of BV1ML4112719: 乔羽 词; 高如星 曲"], "film 汾水长流 insert; year = film year from knowledge (web search says 1960s); 466 s clip is from the film"),
 ("社员都是向阳花", "BV1NU4y1g77U", "张士燮", "王玉西", 1963, "first_performance", "全国 (北方民歌风)", "郭兰英", "original",
  ["bilibili title of BV1vLrjBrEgo: 王玉西 词; 张士燮 曲; 1960年代", "uploader of BV1NU4y1g77U: 1963 concert"], "composition year unchecked; credits come from a Bilibili title only"),
 ("英雄赞歌", "BV1Ez4y1h7Sf", "刘炽", "公木", 1964, "composition", "全国 (军旅)", "张映哲 (领唱)", "original",
  [HY + "1964-Ying-Xiong-Zan-Ge.html", CP100], "film 英雄儿女 version"),
 ("毛主席的话儿记心上", "BV1yg4y157Um", "傅庚辰", "傅庚辰", 1965, "composition", "华北 (冀中)", "邓玉华", "original",
  [ZW + "毛主席的话儿记心上", CP100], "film 地道战; Wikipedia: 邓玉华 first sang it"),
 ("边疆处处赛江南", "BV1iU4y1b71W", "田歌", "袁鹰", 1965, "composition", "新疆", "雷良萍", "original",
  [CP100], "CP100 gives '1960s'; year 1965 is NOT sourced, treat as approximate; 雷良萍 original per uploader"),
 ("情深谊长", "BV1g14y1r7NS", "臧东升", "王印泉", 1962, "composition", "西南多民族 (彝族风格, 据舞蹈改编)", "邓玉华", "original",
  [CP100], "item from the 东方红 epic (1964 stage); idiom note from knowledge"),
 ("没有共产党就没有新中国", "BV1As4y1i7Ut", "曹火星", "曹火星", 1943, "composition", "华北 (抗日根据地)", "杨洪基", "later_cover",
  [CP100], "clip is a 99 s concert excerpt"),
 ("小白杨", "BV19S4y1F7qm", "士心 (初稿 生茂)", "梁上泉", 1983, "composition", "全国 (军旅)", "阎维文", "original",
  [CP100, "web search (Wikipedia/People's Daily items): 梁上泉 wrote lyrics 1983; 生茂 first setting, 士心 final"], "first sung by 阎维文 at the 1983 August 1 party"),
 ("我爱你塞北的雪", "BV11Z4y1j7cr", "刘锡津", "王德", 1980, "composition", "东北部平原", "殷秀梅", "canonical_cover",
  [CP100], "uploader of BV1scHo6sEoh names 周琪华 as first singer"),
 ("泉水叮咚响", "BV1zW4y1z7RZ", "吕远", "马金星", 1982, "composition", "全国 (儿童/抒情民歌风)", "于淑珍", "original",
  [HY + "1982-Quan-Shui-Ting-Dong-Xiang.html"], "film 泉水叮咚; HY original performer 于淑珍 (another uploader says 卞小贞)"),
 ("黄土高坡", "BV1hf421X785", "苏越", "陈哲", 1988, "composition", "西北部高原 (陕北)", "杭天琪", "later_cover",
  [HY + "1988-Huang-Tu-Gao-Po.html"], "HY: original singer 胡月; this is a later recording"),
 ("在那桃花盛开的地方", "BV1cKEKzEEWW", "铁源", "邬大为、魏宝贵", 1981, "composition", "全国 (抒情民歌风)", "董振厚", "original",
  [HY + "1981-Zai-Na-Tao-Hua-Sheng-Kai-De-Di-Fang.html"], "uploader dates 董振厚 first recording 1980"),
 ("我爱五指山我爱万泉河", "BV1934y197bx", "刘长安", "郑南", 1973, "first_publication", "海南", "李双江", "canonical_cover",
  [ZW + "我爱五指山，我爱万泉河", CP100], "first printed 1973 in 战地新歌 (Wikipedia); 李双江 sang it from 1973; this clip is 1983"),
 ("红星照我去战斗", "BV1kt411T7cD", "傅庚辰", "王汝俊", 1974, "composition", "赣 (江西)", "李双江", "original",
  [HY + "1974-Hong-Xing-Zhao-Wo-Qu-Zhan-Dou.html"], "film 闪闪的红星"),
 ("小小竹排江中游", "BV1G34y1r7Sc", "傅庚辰", None, 1974, "composition", "赣 (江西)", "李双江", "original",
  ["web search: 傅庚辰 wrote the film score Nov 1973 in Jingdezhen; film 1974"], "lyricist not sourced"),
 ("青藏高原", "BV18Z42187k7", "张千一", "张千一", 1994, "composition", "藏族 (青藏)", "李娜", "original",
  [HY + "1994-Qing-Zang-Gao-Yuan.html", CP100], ""),
 ("天路", "BV1Gh411D7aP", "印青", "屈塬", 2001, "composition", "藏族", "韩红", "canonical_cover",
  [ZW + "天路", CP100], "Wikipedia: written 2001 for the Qinghai-Tibet railway, first sung by 巴桑, popularised by 韩红 in 2005"),
 ("纤夫的爱", "BV1vx411t7sW", "李凡", "赵小源", 1994, "composition", "西北部高原 (黄河纤夫)", "尹相杰、于文华", "original",
  [HY + "1994-Qian-Fu-De-Ai.html"], "composer name as HY prints it (李凡)"),
 ("最美还是我们新疆", "BV1QxtkePE8U", "吾布力·托乎提", "赵思恩", 1995, "composition", "新疆", "巴哈尔古丽", "original",
  [CP100], ""),
 ("好日子", "BV1vt41167HF", "李昕", "车行", 1997, "composition", "全国 (喜庆民歌风)", "宋祖英", "original",
  [CP100], "1998 gala recording per uploader title"),
 ("走出喜马拉雅", "BV14G411n7hu", "桑诺", "旺堆、桑诺", 2005, "composition", "藏族", "琼雪卓玛", "original",
  [HY + "2005-Zou-Chu-Xi-Ma-La-Ya.html"], ""),
 ("吉祥三宝", "BV1wJ41137iV", "布仁巴雅尔", "布仁巴雅尔", 2005, "composition", "北方草原 (蒙古族)", "布仁巴雅尔、乌日娜、英格玛", "original",
  ["web search (Beijing News / Wikipedia 布仁巴雅尔): on 2005 album 天边, written for his daughter"], ""),
 ("火火的姑娘", "BV1B54y1Y79k", "赵真", "赵真", 2013, "composition", "北方草原 (蒙古族风格)", "东方红艳", "original",
  [HY + "2013-Huo-Huo-De-Gu-Niang.html"], ""),
 ("套马杆", "BV1pJizBzEks", "郭永利", "刘新圈", 2010, "first_recording", "北方草原 (蒙古族风格)", "乌兰托娅", "original",
  ["web search (moegirl 套马杆): 郭永利 曲, 刘新圈 词; first sung 2010"], "year approximate, not firmly sourced"),
 ("怀念战友", "BV1mT4y1u7iZ", "雷振邦", None, 1963, "first_publication", "新疆 (塔吉克)", "李世荣", "original",
  [ZW + "冰山上的来客_(电影)"], "film 冰山上的来客 (1963); lyricist not sourced"),
 # ---- backups ----
 ("高原之歌", "BV1oh4y127TC", "雷振邦", "白辛", 1963, "first_publication", "新疆 (塔吉克)", "吴雁泽", "later_cover",
  ["bilibili title of BV1oh4y127TC: 雷振邦 曲; 白辛 词", ZW + "冰山上的来客_(电影)"], "backup; film year from Wikipedia, credits from uploader title"),
 ("阿里山的姑娘 (高山青)", "BV19t411T7Rn", "周蓝萍", "邓禹平", 1949, "composition", "闽台 (台湾高山族风格)", "奚秀兰", "canonical_cover",
  ["https://n.yam.com/Article/20140206091506", HY + "1949-A-Li-Shan-De-Gu-Niang.html"], "backup; sources conflict: HY names 张彻 (music) and 邓禹飞, Taiwan sources 周蓝萍 and 邓禹平"),
 ("金瓶似的小山", "BV1GHAJe3Ejz", "冰河", "朱丁", 1960, "composition", "藏族 (青海)", "傅丽坤", "canonical_cover",
  [HY + "1960-Jin-Ping-Shi-De-Xiao-Shan.html"], "backup; uploader calls it a Tibetan folk song arranged by 冰河, so it may be folk_adapted"),
 ("乌苏里船歌", "BV1CwN96uECK", "汪云才、郭颂 (据赫哲族曲调)", "胡小石", 1962, "composition", "东北部平原 (赫哲族)", "郭颂", "original",
  [HY + "1962-Wu-Su-Li-Chuan-Ge.html"], "backup; based on a Hezhe tune, authorship is disputed, may be folk_adapted; 1963 first recording per uploader"),
 ("红星歌", "BV1WU4y1C71K", "傅庚辰", "邬大为、魏宝贵", 1974, "composition", "赣 (江西)", None, "original",
  [CP100], "backup; short clip, singer not named, may be children's chorus"),
 ("手拿碟儿敲起来", "BV1CL4y1n7fu", "张敬安、欧阳谦叔 等 (洪湖赤卫队集体创作)", "梅少山 等 (集体创作)", 1958, "composition", "江汉 (湖北)", "李金梅", "original",
  [ZW + "洪湖赤卫队_(歌剧)"], "backup; opera was written collectively in 1958; song-level credits not checked"),
 ("洪湖水浪打浪", "BV1iq4y137yE", "张敬安、欧阳谦叔 等 (洪湖赤卫队集体创作)", "梅少山 等 (集体创作)", 1958, "composition", "江汉 (湖北)", "电影原声 (王玉珍)", "original",
  [ZW + "洪湖赤卫队_(歌剧)", HY + "1961-Hong-Hu-Shui-Lang-Da-Lang.html"], "backup; same song already in corpus as other recordings; tune taken from 襄河谣"),
 ("梦驼铃", "BV1Q84y1T7vH", "谭健常", "小轩", 1984, "composition", "西北部高原 (丝路)", "谭健常", "later_cover",
  [HY + "1984-Meng-Tuo-Ling.html"], "backup; HY lists 费玉清 as original performer"),
 ("绣红旗", "BV1A6x8eEEdk", "羊鸣、姜春阳、金砂", "阎肃", 1964, "composition", "西南 (四川民歌风)", "铁金等", "later_cover",
  ["knowledge"], "backup; authorship from knowledge only (same team as 红梅赞)"),
 ("我爱你，中国", "BV1sr421M7Qm", "郑秋枫", "瞿琮", 1979, "composition", "无 (非民歌风)", "叶佩英", "canonical_cover",
  [CP100], "backup; not folk idiom, contrast of a composed art song; CP100 dates 1979, HY 1980"),
 ("我和我的祖国", "BV1UE411R7id", "秦咏诚", "张藜", 1985, "composition", "无 (非民歌风)", "李谷一", "original",
  [CP100], "backup; not folk idiom"),
 ("大海啊故乡", "BV1Xg411g7Fh", "王立平", "王立平", 1983, "composition", "无 (非民歌风)", "朱明瑛", "original",
  [CP100], "backup; not folk idiom"),
 ("让我们荡起双桨", "BV1XW4y167Vc", "刘炽", "乔羽", 1955, "composition", "无 (非民歌风)", "电影原声", "original",
  [CP100, HY + "1955-Rang-Wo-Men-Dang-Qi-Shuang-Jiang.html"], "backup; children's film song, not folk idiom"),
]


def load_log():
    hits, first_q = {}, {}
    for line in LOG.read_text().splitlines():
        d = json.loads(line)
        for h in d["hits"]:
            hits.setdefault(h["id"], h)
            first_q.setdefault(h["id"], d["query"])
    return hits, first_q


def main():
    hits, first_q = load_log()
    out, seen = [], set()
    for (song, vid, comp, lyr, yr, yk, idiom, singer, ptype, srcs, note) in E:
        h = hits.get(vid)
        assert h, f"{vid} ({song}) not in search log"
        assert 60 <= h["duration_s"] <= 600, f"{vid} ({song}) duration {h['duration_s']}"
        assert vid not in seen, vid
        seen.add(vid)
        out.append({
            "platform": "bili", "id": vid, "url": h["url"], "title": h["title"], "channel": h["channel"],
            "channel_id": h["channel_id"], "duration_s": h["duration_s"], "song_name": song,
            "composer": comp, "lyricist": lyr, "year": yr, "year_kind": yk, "idiom_region": idiom,
            "singer": singer, "performance_type": ptype, "sources": srcs,
            "source_query": first_q[vid], "note": note,
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"region": "创作民歌", "candidates": out}, ensure_ascii=False, indent=1))
    print(len(out), "candidates ->", OUT)


if __name__ == "__main__":
    main()
