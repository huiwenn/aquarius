import csv, os
OUT = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/regions_curated/song_dates"
COLS = ["song_name","region","song_type","origin_period","earliest_attestation_year","attestation_source",
        "composer_or_adapter","composition_or_adaptation_year","evidence_urls","confidence","notes"]
T, TA, NC, U = "traditional", "traditional-adapted", "newly-composed-folk-style", "unknown"

# URL shorthands
HAKKA = "https://www.ihchina.cn/project_details/12424.html ; https://zh.wikipedia.org/zh-hans/%E5%AE%A2%E5%AE%B6%E5%B1%B1%E6%AD%8C"
TWHAKKA = "https://zh.wikipedia.org/zh-hans/%E4%B9%9D%E8%85%94%E5%8D%81%E5%85%AB%E8%AA%BF ; https://zh.wikipedia.org/zh-hans/%E5%AE%A2%E5%AE%B6%E5%B1%B1%E6%AD%8C"
XSG = "https://www.ihchina.cn/project_details/12425 ; https://zh.wikipedia.org/zh-hans/%E5%92%B8%E6%B0%B4%E6%AD%8C ; https://dfz.gd.gov.cn/index/dqyj/whyj/content/post_2597976.html"
MUYU = "https://www.ihchina.cn/project_details/13754/ ; https://zh.wikipedia.org/zh-hans/%E6%9C%A8%E9%AD%9A%E6%AD%8C"
MAIJI = "https://www.sohu.com/a/383642031_100017614"
DANZHOU = "http://www.ihchina.cn/project_details/11285 ; https://zh.wikipedia.org/zh-hans/%E5%84%8B%E5%B7%9E%E8%B0%83%E5%A3%B0"
CANTO_RHYME = "https://www.gznf.cn/story/98060.html ; https://zh.wikipedia.org/wiki/%E7%B2%B5%E8%AA%9E%E7%AB%A5%E8%AC%A0"
WEIRAN = "https://news.qq.com/rain/a/20250417A07Z7600 ; http://www.people.com.cn/24hour/n/2013/0817/c25408-22596969.html"
MIANYANG = "https://baike.baidu.com/item/%E6%B2%94%E9%98%B3%E6%B0%91%E6%AD%8C/10417120 ; https://www.tianmen.gov.cn/zjtm/rwls/whyc/201606/t20160616_1931618.shtml"
TUJIA = "https://www.ihchina.cn/project_details/12793/"
SANGZHI = "https://www.ihchina.cn/project_details/12423/ ; https://m.thepaper.cn/baijiahao_7412899"
DONGTING = "https://www.ihchina.cn/art/detail/id/12794.html ; https://www.yueyang.gov.cn/yywh/whyc/fwzwhyc/content_201252.html"
JIAHE = "https://whhlyt.hunan.gov.cn/whhlyt/news/sxxw/202306/t20230628_29386357.html ; https://hn.rednet.cn/content/2021/09/17/10153872.html"
NUSHU = "https://zh.wikipedia.org/zh-hans/%E5%A5%B3%E4%B9%A6"
GANNAN = "https://baike.baidu.com/item/%E9%BB%84%E7%8E%89%E8%8B%B1/5768144"
XINGGUO = "https://www.xingguo.gov.cn/xgzf/c114408/201107/284f708af42246e5b30a82059089c6e9.shtml ; https://www.ihchina.cn/Article/Index/detail?id=8329"
SONGLANG = "https://www.chinanews.com.cn/sh/2011/05-26/3068359.shtml ; https://epaper.gmw.cn/gmrb/html/2014-09/17/nw.D110000gmrb_20140917_1-05.htm"
NA = "NA"

def r(name, typ, period=NA, year=NA, src=NA, comp=NA, cyear=NA, urls=NA, conf="low", notes=""):
    return dict(song_name=name, song_type=typ, origin_period=period, earliest_attestation_year=year,
                attestation_source=src, composer_or_adapter=comp, composition_or_adaptation_year=cyear,
                evidence_urls=urls, confidence=conf, notes=notes)

G_TRAD = "Anonymous oral tradition; no song-level dating found."

DATA = {
"粤": [
 r("临高渔歌（哩哩美）", T, urls=NA, notes="Genre label (Lingao fishing song, 哩哩美). No source retrieved (web search budget exhausted); no dating recorded."),
 r("久久不见久久见", NC, "1980s", "1986", "Song first published/premiered 1986 (zh.wikipedia)", "谢文经", "1986", "https://zh.wikipedia.org/zh-hans/%E4%B9%85%E4%B9%85%E4%B8%8D%E8%A6%8B%E4%B9%85%E4%B9%85%E8%A6%8B ; https://news.rednet.cn/content/2018/04/10/4795821.html", "high", "Inspired by 1979 fieldwork at 五指山水满乡 and released 1986. Often labelled 海南民歌 or 黎族民歌, but it has a known composer."),
 r("五指山歌", TA, "Republican (1912–1949)", "1948", "Adapted c.1948 by 琼崖纵队文工团 from the Li 罗尼调 (Hainan Zhoukan 2022)", "吴乾鹏 (lyrics); 琼崖纵队文工团", "1948", "https://www.hainanfp.com/xinwen/2022/show-3625.html ; https://baike.baidu.com/item/%E4%BA%94%E6%8C%87%E5%B1%B1%E6%AD%8C/4381027", "medium", "The year is given as approximate ('约1948'). The tune later supplied material for 万泉河水清又清."),
 r("儋州调声（传统）", T, "late Qing (genre)", "1909-1911", "Earliest collected 调声 texts date from the 宣统 reign (genre-level, ihchina)", urls=DANZHOU, conf="medium", notes="Genre-level dating; no individual song identified. A claim of Western Han origin is legend. National 非遗 2006."),
 r("儋州调声（本土唱法）", T, "late Qing (genre)", "1909-1911", "Earliest collected 调声 texts date from the 宣统 reign (genre-level, ihchina)", urls=DANZHOU, conf="medium", notes="Genre-level dating; this is a live local performance and the piece is not identified. A claim of Western Han origin is legend."),
 r("卖懒", T, urls="https://ep.ycwb.com/epaper/ycwb/html/2020-01/27/content_7_232339.htm ; https://www.gz.gov.cn/zlgz/whgz/content/post_8051423.html", conf="low", notes="The New Year's Eve custom (as 卖冷) is recorded in 屈大均《广东新语》 (early Qing), but that source does not document the song text itself, so year = NA."),
 r("卖鸡调·懒婆娘", T, "late Qing (genre)", "1957", "杨达 took 《懒婆娘》 to the Guangdong music & quyi troupe in 1957 (Kaiping 非遗 page)", urls=MAIJI, conf="low", notes="《开平县文化志》 says 卖鸡调 was popular in the late Qing. The source is about 开平卖鸡调, but this recording is labelled 台山; the two are neighbouring 五邑 variants."),
 r("卖鸡调·退聘禮", T, "late Qing (genre)", urls=MAIJI, conf="low", notes="Genre-level period only (《开平县文化志》). No song-level dating."),
 r("卖鸡调（老一辈唱法）", T, "late Qing (genre)", urls=MAIJI, conf="low", notes="Genre-level period only. The piece is not identified."),
 r("叫侬唱歌侬就唱", NC, "1950s–1960s", NA, NA, "王妚大 (Li folk singer)", "1955-1963", "https://www.ihchina.cn/character_detail/8827.html", "low", "ihchina credits 王妚大 with creating the song between 1955 and 1963. This recording is sung in Hainanese; it may be a different song with the same title."),
 r("咸水歌·十八相送", T, urls=XSG, notes="Genre (疍歌) is described in 屈大均《广东新语》 (late 17th c.). The narrative is borrowed from 梁祝. No song-level date. National 非遗 2006 (中山咸水歌)."),
 r("咸水歌·陈世美", T, urls=XSG, notes="Genre described in 《广东新语》 (late 17th c.). The story comes from opera and 木鱼书 repertoire. No song-level date."),
 r("咸水歌（中山，曲目未标）", T, urls=XSG, notes="Piece not identified. Genre described in 《广东新语》 (late 17th c.); national 非遗 2006."),
 r("嘆生禮·嘆阿爹", T, urls=XSG, notes="疍家 lament (叹歌). " + G_TRAD),
 r("嘱姑九点半", TA, NA, NA, NA, "洪万儒 (credited lyrics/music); 陈文清 (orchestration)", NA, "https://view.inews.qq.com/a/20200929A0FRTX00 ; " + DANZHOU.split(' ; ')[0], "low", "Credits conflict: some releases name 洪万儒 as writer, others call it 民间调声. It became widely known in 2020."),
 r("大澳舢舨歌謠", T, urls=XSG, notes="Hong Kong 咸水歌 (HK ICH inventory 2014, genre). " + G_TRAD),
 r("摇侬调", T, urls="https://www.ihchina.cn/project_details/12427", notes="崖州民歌 lullaby. Sources disagree on the genre's origin (Song vs Ming claims), which are undocumented. No song-level date."),
 r("攞魚歌", T, urls=XSG, notes="Macau 咸水歌 (Macau ICH 2020, genre). " + G_TRAD),
 r("月光光", T, NA, "1936", "Recording by child star 黎铿, 1936 (per the uploaded recording's title; not independently verified)", urls=CANTO_RHYME + " ; https://zh.wikipedia.org/zh-cn/%E6%9C%88%E5%85%89%E5%85%89_(%E5%84%BF%E6%AD%8C)", conf="low", notes="Guangfu rhyme. 刘万章《广州儿歌甲集》 (1928) is the earliest systematic print collection, but it was not verified to contain this title. Song/Ming origin claims are undocumented."),
 r("木魚歌·陳世美", T, "late Ming (genre)", urls=MUYU, conf="low", notes="The 木鱼书 genre is documented from late Ming, and 《陈世美三官堂》 is a 木鱼书 title. No song-level date."),
 r("木鱼金兰腔·情歌对唱", T, "late Ming (genre)", urls=MUYU, notes="Genre-level period only."),
 r("木鱼（台山阿姆唱）", T, "late Ming (genre)", urls=MUYU, notes="Genre-level period only. The piece is not identified."),
 r("水乡情（高堂歌）", U, urls=XSG, notes="高堂歌 is a 咸水歌 tune. The title 水乡情 may be a newer lyric; provenance not found."),
 r("氹氹转", TA, NA, NA, NA, "韦然 (melody/arrangement)", "1976-1978", WEIRAN, "medium", "Traditional Guangfu rhyme text. The widely sung tune is by 韦然 (1976–78 cycle); it is assumed, not verified, that this recording uses his setting."),
 r("汕尾渔歌", T, notes="汕尾疍家渔歌 (channel labels it Teochew/Swabue). No source retrieved; no dating."),
 r("汕尾渔歌·斗歌", T, notes="汕尾疍家渔歌. No source retrieved; no dating."),
 r("海底珍珠容易搵", T, urls=XSG, notes="中山咸水歌. Authorship and date not established."),
 r("禾樓歌（山歌論籮勿論篇）", T, notes="台山 禾楼歌 (harvest antiphonal). No source retrieved; no dating."),
 r("落雨大", T, urls=CANTO_RHYME + " ; http://www.people.com.cn/24hour/n/2013/0817/c25408-22596969.html", conf="low", notes="Traditional Guangfu rhyme. A new sung version (《落大雨》) came out of Guangdong's 1955–60 collection campaign; the CCTV performance probably uses such a later setting (arranger unknown)."),
 r("蜑家船歌", T, urls=XSG, notes=G_TRAD),
 r("行船歌（大船拋住沱濘頭）", T, urls=XSG, notes=G_TRAD),
 r("賀年歌", T, notes="台山 New Year song by a blind folk artist. No source retrieved."),
 r("鸡公仔", TA, NA, "1928", "刘万章《广州儿歌甲集》 (国立中山大学, 1928) contains 9 variants", "韦然 (melody)", "1978", CANTO_RHYME + " ; " + WEIRAN.split(' ; ')[1], "medium", "Some sources give the collection year as 1927. The text's meaning changed over time (bride lament → wartime → children's moral). This recording is from 韦然's channel, so it uses his 1978 setting."),
 r("龙舟歌（龙舟说唱）", T, urls="https://zh.wikipedia.org/zh-hans/%E9%BE%99%E8%88%9F%E6%AD%8C", notes="Traditionally said to have formed in the Qianlong era (Shunde), but Wikipedia notes there is no formal record, so period = NA. National 非遗 2006."),
],
"客家特区": [
 r("丰顺山歌", T, urls=HAKKA, notes="Genre label. " + G_TRAD),
 r("兴宁山歌", T, urls=HAKKA, notes="Genre label. " + G_TRAD),
 r("十二月古人", T, urls=TWHAKKA, notes="Taiwan Hakka narrative song (archival 鄧滿妹/陳秀鳳). " + G_TRAD),
 r("十跌古", T, urls=HAKKA, notes=G_TRAD),
 r("半山謠", T, urls=TWHAKKA, notes="美浓 (六堆) tune type. " + G_TRAD),
 r("天公落水", T, urls="https://www.wpchen.net/en/posts/tian-gong-luo-shui ; https://ssl.thcp.org.tw/libraries/songs/59", conf="medium", notes="Credited as 古词/传统 in multiple arrangements (楊燦明 2010, 蔡昱姍 2015, 戴陽 2015). The 古慧慧 recording's arranger is unknown."),
 r("嬲到日頭轉西山", T, urls=HAKKA, notes=G_TRAD),
 r("客家山歌好出名", T, urls=HAKKA, notes=G_TRAD),
 r("客家山歌对唱（五华妹与93岁阿婆）", T, urls=HAKKA, notes="Improvised duet; not a fixed song."),
 r("客家山歌（91岁阿婆）", T, urls=HAKKA, notes="Improvised/unidentified piece."),
 r("客家山歌（传统）", T, urls=HAKKA, notes="Piece not identified."),
 r("客家山歌（龙岩）", T, urls=HAKKA, notes="Field recording; piece not identified."),
 r("客家盘歌", T, urls=HAKKA, notes="浏阳 Hakka riddle-duet genre. " + G_TRAD),
 r("山歌仔·冬梅", T, urls=TWHAKKA, notes="山歌仔 is a traditional Taiwan Hakka tune type; lyric authorship is not established."),
 r("山歌子·客家花", T, urls=TWHAKKA, notes="山歌子 tune type is traditional; the lyric title may be newer (not established)."),
 r("平板", T, urls=TWHAKKA, notes="Tune type (平板调) that developed from 老山歌/山歌子; genre-level, no date."),
 r("平板·飲水思源", T, urls=TWHAKKA, notes="平板 tune type is traditional; lyric authorship not established."),
 r("广东上来一个人", T, urls=HAKKA, notes="浏阳 Hakka; the lyric refers to migration from Guangdong. " + G_TRAD),
 r("摇篮歌", T, urls=TWHAKKA, notes="美浓 lullaby. " + G_TRAD),
 r("月光光", T, urls="https://www.chinanews.com/sh/2015/06-20/7357084.shtml", notes="Hakka nursery rhyme ('源于何时，史无记载'). This is the 赣南 recording."),
 r("月光光秀才郎", T, urls="https://www.chinanews.com/sh/2015/06-20/7357084.shtml", notes="Hakka nursery rhyme; no documented origin."),
 r("月光光（客家童謠）", T, urls="https://www.chinanews.com/sh/2015/06-20/7357084.shtml", notes="Taiwan Hakka version; no documented origin."),
 r("有好山歌溜等来", T, urls=HAKKA, notes="贺州 Hakka. " + G_TRAD),
 r("梅州传统山歌·情歌对唱", T, urls=HAKKA, notes="Piece not identified."),
 r("梅縣情歌", T, NA, "1956", "Recorded in Hong Kong 1956 by 李南華 and 吳超文 of 中國民間藝術團 (per recording metadata)", urls=HAKKA, conf="medium", notes="The attestation is the recording itself. No earlier date found."),
 r("犁田歌", T, urls=HAKKA, notes="Work song. " + G_TRAD),
 r("百花山上", T, urls=HAKKA, notes=G_TRAD),
 r("竹叶撑船你爱来", T, urls=HAKKA, notes="Labelled 传统山歌 on release; no dating."),
 r("老十二月古人", T, urls=TWHAKKA, notes="Taiwan Hakka (徐木珍). " + G_TRAD),
 r("老妹好比桂花树", T, urls=HAKKA, notes="浏阳 Hakka. " + G_TRAD),
 r("老山歌", T, urls=TWHAKKA, notes="Oldest Taiwan Hakka tune type (genre-level); no date."),
 r("老山歌·採茶", T, urls=TWHAKKA, notes="老山歌 tune type; lyric authorship not established."),
 r("落水天", T, urls="https://baike.baidu.com/item/%E8%90%BD%E6%B0%B4%E5%A4%A9/9496242 ; " + HAKKA.split(' ; ')[0], notes="Widespread across Hakka areas (Guangdong, Fujian, Jiangxi, Taiwan). No dating."),
 r("送郎", T, urls=TWHAKKA, notes="Taiwan Hakka (陳明珠; 古堂財/李喜娣 美浓 versions). " + G_TRAD),
 r("送郎过番", T, "Qing–Republican (genre 过番歌)", urls=HAKKA, conf="low", notes="过番歌 (emigration songs) are described as sung by Qing-era emigrants. Period is genre-level; no song-level date."),
 r("采桑歌", T, urls=HAKKA, notes=G_TRAD),
 r("闽西山歌", T, urls=HAKKA, notes="Genre label (吴金发). " + G_TRAD),
 r("阿哥出门往南洋", T, "Qing–Republican (genre 过番歌)", urls=HAKKA, conf="low", notes="Emigration-to-Nanyang theme (过番歌 genre). Period is genre-level only."),
],
"江汉": [
 r("一把芝麻撒上天", T, urls="https://ctdsb.net/c1676_202410/2271485.html", notes="Labelled 浠水民歌. Provenance and date not found."),
 r("一支山歌飞出崖", U, notes="Labelled 湖北民歌 (周友金 album). No information found on origin or authorship."),
 r("伙计歌", T, urls=TUJIA, notes="Traditional Enshi Tujia song; no author found. A 《伙计调》 from 荆州马山 was printed in 《中国民歌》 vol.1 (1980), but it may be a different song."),
 r("信阳民歌", T, notes="Field recording of unidentified Xinyang (Henan) folk song."),
 r("催咚催", T, urls="https://baike.baidu.com/item/%E5%82%AC%E5%92%9A%E5%82%AC/12687592 ; https://www.jianshu.com/p/ab1ab2d341c7", conf="medium", notes="潜江/沔阳 threshing work song (from 《打莲香》). A claimed link to the 诗经/楚 扬歌 is not evidence. National 非遗 2008 (潜江民歌)."),
 r("六口茶", T, NA, "2002", "Transcribed 2002 by 甘武 from 谢小平; printed 2005 in an internal 恩施市 song collection; 2009 《恩施市民间歌曲集》", urls="https://www.chinanews.com/cul/2012/09-06/4163181.shtml ; https://www.chinafolklore.org/web/index.php?NewsID=10697", conf="medium", notes="The source singer 魏明清 learned it in the 1970s from 石明哲. Its place of origin is disputed. The song may be of fairly recent origin."),
 r("利川小曲", T, urls="http://iel.cass.cn/fwzwhycbh/zgsj/200712/t20071229_2763677.shtml", notes="Narrative singing genre, one of Lichuan's 'three treasures'. No dated origin found."),
 r("到春来呀百花开呀", T, urls=MIANYANG, notes="沔阳民歌. " + G_TRAD),
 r("卖篾货", T, urls="https://baike.baidu.com/item/%E5%91%A8%E5%8F%8B%E9%87%91/9742051", notes="长阳民歌 in 周友金's repertoire. No dating."),
 r("卖马调", T, urls="https://baike.baidu.com/item/%E5%91%A8%E5%8F%8B%E9%87%91/9742051", notes="长阳民歌. No dating."),
 r("反照花台", T, urls=MIANYANG, notes="沔阳民歌. " + G_TRAD),
 r("哪有闲空回娘家", T, NA, "1958", "蒋桂英 sang 《回娘家》 at the 1958 national folk music festival (怀仁堂) and it was issued on disc (1958 record per upload)", urls="https://www.tianmen.gov.cn/zjtm/tmwh/tmmr/201604/t20160419_1930933.shtml", conf="medium", notes="沔阳/天门 小调. The attestation is the 1958 performance/record."),
 r("啰啰咚", T, urls="https://www.ihchina.cn/project_details/12620/", conf="medium", notes="监利 rice-transplanting work song (genre). Claims of Warring States 楚声 ancestry and the 刘禹锡 mention are about field-song practice, not this song. National 非遗 2008."),
 r("嗺咚嗺", T, urls="https://baike.baidu.com/item/%E5%82%AC%E5%92%9A%E5%82%AC/12687592", conf="medium", notes="Same song as 催咚催 (variant spelling)."),
 r("土家迎客歌", TA, NA, NA, NA, "田隆信 (collector); 杨军 (arranger)", NA, "https://hy.ktvc8.com/mobile/422503_1.html", "low", "Several versions exist: a traditional Tujia greeting song collected by 田隆信 and arranged by 杨军, and a separate composition by 夏劲风/余方华. It is unclear which one the CCTV performance uses."),
 r("太阳过了河", U, notes="Labelled 十堰民歌 (杨华, 民歌中国). No information found on authorship or date."),
 r("姑娘送你咚咚锵", T, urls=MIANYANG, notes="沔阳民歌. " + G_TRAD),
 r("幸福歌", NC, "1950s", "1959", "Recorded and released 1959 (Central Radio broadcast)", "何火 (lyrics); 蒋桂英 (arr./singer)", "1958", "https://news.qq.com/rain/a/20210705A07T3600 ; https://baike.baidu.com/item/%E5%B9%B8%E7%A6%8F%E6%AD%8C/10364093", "high", "Great Leap Forward-era new folk song built on 天门 小调 and the 薅草歌 melody."),
 r("撒叶儿嗬（跳丧）", T, urls="https://www.ihchina.cn/zhengce_details/11546 ; http://wlt.hubei.gov.cn/hbsfwzwhycw/bhcc/fydt/esz/202005/t20200525_2295638.shtml", conf="medium", notes="Tujia funeral dance-song. 樊绰《蛮书》 (Tang) describes Ba funerary drumming and dancing; that is ancestral practice, not evidence for this repertoire. National 非遗 2006."),
 r("月望郎", T, urls=MIANYANG, notes="沔阳民歌. " + G_TRAD),
 r("洪湖水浪打浪", NC, "1950s", "1959", "Premiered in the opera 《洪湖赤卫队》 by 湖北省实验歌剧团, 1959; film version 1961", "张敬安, 欧阳谦叔 (music); 梅少山 et al. (lyrics)", "1958", "https://www.thepaper.cn/newsDetail_forward_12130209 ; https://baike.baidu.com/item/%E6%B4%AA%E6%B9%96%E6%B0%B4%E6%B5%AA%E6%89%93%E6%B5%AA", "high", "Written in the style of 洪湖 fishermen's songs, after fieldwork at 沙口镇."),
 r("神农架花鼓歌", T, notes="Genre label. No source retrieved."),
 r("神农溪土家族山歌", T, urls=TUJIA, notes="Genre label (巴东 Tujia). " + G_TRAD),
 r("绣荷包", T, "mid-Qing (title family)", "1980", "马山 version printed in 《中国民歌》 vol.1 (上海文艺出版社, 1980)", urls="https://www.ihchina.cn/project_details/12611 ; http://www.jzqwhg.org.cn/detail-1748.html", conf="medium", notes="The 绣荷包 小曲 family is attested in 《白雪遗音》 (1828) according to 傅惜华, but that text is not necessarily this 马山 tune. 马山民歌 is national 非遗."),
 r("补背褡", T, urls=MIANYANG, notes="沔阳民歌. " + G_TRAD),
 r("车水情歌", T, urls="https://www.tianmen.gov.cn/zjtm/tmwh/mjys/201604/t20160419_1931080.shtml", notes="Jianghan-plain water-pumping song type (车水歌). The popular stage version may be arranged; no arranger found."),
 r("黄四姐", T, "late Qing (local claim)", "1958", "Staged at provincial level after arrangement by cultural workers, 1958; first public Wuhan performance 1964", urls="http://www.cnhubei.com/xw/wh/201209/t2222826.shtml ; http://tujiazu.com.cn/index.php/Archives/IndexArchives/index/a_id/2044.html", conf="medium", notes="建始 喜花鼓, earlier called 货郎歌. The '150 years' age and the 黄幺姑 origin story are local tradition (legend). The 1958 arrangers are not named. Hubei provincial 非遗 2007."),
 r("龙船调", TA, NA, "1953-1956", "种瓜调 recorded from 丁鸿儒 by 周叙卿 (1953, some sources) or collected at 柏杨坝 by 周叙卿 and 黄业威 (Feb 1956)", "周叙卿, 黄业威 (collection/adaptation)", "1956", "https://www.zgwypl.com/content/details81_48939.html ; https://news.gmw.cn/2025-04/13/content_37962732.htm", "medium", "Sources disagree on the collection date (1953 vs 1956). The adaptation cut 10 verses to 2 and renamed it 龙船调; tune and refrain unchanged. 利川灯歌 (genre) is said to date from early Qing."),
],
"湘": [
 r("一根竹竿容易弯", TA, "Republican (1912–1949)", NA, NA, "宋扬", "1946-1948", "https://www.sohu.com/a/155719728_99895911", "low", "Said to have been created in 1946–48 while 宋扬's drama troupe worked in 长沙/衡阳; 宋扬 is credited in teaching materials. The tune is from central Hunan and the lyrics are in 长沙 dialect. Whether it is a composition or an arrangement is unclear."),
 r("伴嫁歌", T, urls=JIAHE, conf="medium", notes="嘉禾伴嫁歌 (genre). Collected four times between 1951 and 2005. Tang/Song origin claims are undocumented. Provincial 非遗 2006, national 2021."),
 r("刘海砍樵", TA, "Qing (legend/花鼓戏)", NA, "The 刘海 legend is recorded in the Kangxi and Jiaqing 《常德府志》 (legend, not the song)", "陈北方 (adaptation); 何冬保 et al. (music)", "1951", "https://baike.baidu.com/item/%E5%88%98%E6%B5%B7%E7%A0%8D%E6%A8%B5/2449323 ; http://whhlyt.hunan.gov.cn/whhlyt/news/mtjj/201412/t20141223_5421253.html", "medium", "花鼓戏 excerpt. The current version was adapted in 1951 from the older 大砍樵. Hunan 花鼓戏 emerged c. 1736–1820."),
 r("古丈山歌", T, urls="https://zh.wikipedia.org/zh-hans/%E4%BD%95%E7%BA%AA%E5%85%89", notes="何纪光's recording (issued on disc, year unknown). No song-level date."),
 r("召市五句歌", T, urls=TUJIA, notes="龙山 Tujia five-line song. " + G_TRAD),
 r("哭嫁歌", T, urls=TUJIA, notes="Tujia bridal lament genre. " + G_TRAD),
 r("四季花儿开", T, urls="https://zh.wikipedia.org/zh-hans/%E4%BD%95%E7%BA%AA%E5%85%89", notes="Labelled 湖南民歌 and recorded by 何纪光 as a duet. Provenance not established; it may be arranged."),
 r("四川下来蹲蹲儿岩（上四川）", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("坐堂歌", T, notes="湘西 Miao song. No source retrieved."),
 r("姐姐出嫁", T, urls=JIAHE, notes="嘉禾伴嫁歌. " + G_TRAD),
 r("娘试女", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("山歌无姐做不成", T, notes="长沙 folk song. " + G_TRAD),
 r("恰茶歌", T, urls=DONGTING, notes="洞庭渔歌. The 范仲淹 'fishermen's songs answer each other' line (1046) is a literary mention of the practice, not of this song. National 非遗 2014."),
 r("扯白歌", T, urls="https://zh.wikipedia.org/zh-hans/%E4%BD%95%E7%BA%AA%E5%85%89", notes="湘西; 何纪光 recording issued on disc. No song-level date."),
 r("挑担茶叶上北京", NC, "1960s", "1960", "Written 1960 (叶蔚林 lyrics after 衡山 fieldwork); popularised by 何纪光 at 上海之春 1964", "白诚仁 (music); 叶蔚林 (lyrics)", "1960", "https://hunan.voc.com.cn/news/202106/24001837.html ; https://baike.baidu.com/item/%E6%8C%91%E6%8B%85%E8%8C%B6%E5%8F%B6%E4%B8%8A%E5%8C%97%E4%BA%AC/16532537", "high", "Composed in a 湘西/湖南 folk idiom."),
 r("春季劝男", T, notes="长沙 folk song. " + G_TRAD),
 r("板栗开花一条线", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("棒棒捶在岩板上", T, urls=SANGZHI + " ; https://m.fx361.com/news/2019/1216/13028866.html", notes="桑植 Tujia love song. It has an orchestral arrangement by 孟勇; this performance's arranger is unknown."),
 r("槐树花儿香", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("欠姐歌", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("洗菜心", TA, NA, NA, "Earliest documented version (望城) in 《湖南民间歌曲集（长沙市分册）》 (year not found)", "杨福生 (collection/adaptation of the popular 3-verse version)", NA, "https://m.fx361.com/news/2019/0611/8107991.html ; https://baike.baidu.com/item/%E6%B4%97%E8%8F%9C%E5%BF%83/12774497", "medium", "A 长沙–醴陵 小调 with no dated origin, absorbed into 花鼓戏."),
 r("洞庭号子", T, urls=DONGTING, notes="洞庭渔歌 genre. " + G_TRAD),
 r("浏阳河", NC, "1950s", "1951", "Third section of the 花鼓戏 《推土车》/《双送粮》 (written 1950), re-set to the 花鼓 《送瓜调》 in 1951", "徐叔华 (lyrics); 朱立奇, 唐璧光 (music)", "1950-1951", "https://zh.wikipedia.org/wiki/%E6%B5%8F%E9%98%B3%E6%B2%B3_(%E6%AD%8C%E6%9B%B2) ; https://www.chinanews.com.cn/sh/2011/05-06/3020627.shtml ; https://hunan.voc.com.cn/news/202112/23756072.html", "high", "Credited as '湖南民歌' from 1957 until the authors were rehabilitated after 1976. The tune comes from 花鼓戏 《田寡妇看瓜》."),
 r("澧水船夫号子", T, NA, "1956", "Collected by the 中央音乐研究所 team under 杨荫浏 (source spells it 杨英浏), 1956; later staged and won awards abroad", urls="https://www.ihchina.cn/project_details/12483/ ; https://zh.wikipedia.org/wiki/%E6%BE%A7%E6%B0%B4%E8%88%B9%E5%B7%A5%E8%99%9F%E5%AD%90", conf="medium", notes="Boatmen's work songs; a '500 years' figure circulates without documentation. The choral stage arrangements came later."),
 r("特特歌", T, urls=DONGTING, notes="洞庭渔歌. " + G_TRAD),
 r("织锦情歌", T, urls=TUJIA, notes="湘西 Tujia. " + G_TRAD),
 r("芭蕉树上挂红灯", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("蓑衣歌", T, urls=DONGTING, notes="Named in sources as a representative 洞庭渔歌. No date."),
 r("训女词", T, urls=NUSHU, notes="女书 song from 江永. 女书 came to academic attention in 1982 (宫哲兵); no song-level date."),
 r("郎从门前过", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("郎在外间打山歌", T, urls="https://zh.wikipedia.org/zh-hans/%E4%BD%95%E7%BA%AA%E5%85%89", notes="长沙山歌; 何纪光 recording. No date."),
 r("郎在高山打一望", T, urls=SANGZHI, notes="桑植民歌. " + G_TRAD),
 r("采茶（湖南花鼓）", T, notes="花鼓 小调 (鞠秀芳 recording). No source retrieved."),
 r("金坨女", T, urls=NUSHU, notes="女书 song from 江永. No song-level date."),
 r("马桑树儿搭灯台", T, "mid–late Qing (inferred from lyrics)", "1956", "Collected 1956 by 左泽中 (长沙市文化馆) from 周耀榜 at 桑植 樵子湾; sung in Beijing 1957", NA, NA, "https://www.dswxyjy.org.cn/n1/2022/0411/c437095-32396077.html ; https://baike.baidu.com/item/%E9%A9%AC%E6%A1%91%E6%A0%91%E5%84%BF%E6%90%AD%E7%81%AF%E5%8F%B0/9008327", "medium", "The period is a source's inference from the merchant-husband lyric. During the Land Revolution (1927–37), 贺锦斋 wrote revolutionary lyrics to it. The composer is unknown."),
],
"赣": [
 r("上茶山", T, urls=GANNAN, notes="Instrumental rendition (方锦龙) of a 赣南 tune. No dating."),
 r("不唱山歌心不爽", TA, NA, NA, NA, "范光治 (choral arrangement)", NA, NA, "low", "The arranger is named in the upload title only; no year found."),
 r("倒采茶", T, urls=GANNAN, notes="石城 灯歌/采茶 tune (黄玉英). No dating."),
 r("兴国山歌", T, urls=XINGGUO, conf="medium", notes="Genre. A 'Tang 太上隐者' mention in the county gazetteer is legendary. New revolutionary lyrics were set to it in the 1930s Soviet period. National 非遗 2006."),
 r("割韭菜", T, urls=GANNAN, notes="赣南民歌 recorded by 黄玉英 (albums 1990–2004; not song-level evidence)."),
 r("十怨妹", T, notes="Instrumental 赣南采茶调. No source retrieved."),
 r("十送红军", NC, "1960s", "1961", "Performed 1961 by the Air Force Political Dept. song-and-dance troupe", "张士燮 (lyrics); 朱正本 (music)", "1960", SONGLANG + " ; https://baike.baidu.com/item/%E5%8D%81%E9%80%81%E7%BA%A2%E5%86%9B/17553713", "high", "Built on the 赣南采茶 melody 《长歌》/《送郎调》 collected in 1960 fieldwork, so it could also be classed as traditional-adapted. A Shaanxi-vs-Jiangxi origin debate exists (光明日报 2014)."),
 r("双牵手", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("哭嫁", T, notes="遂川 Hakka bridal lament (field video). " + G_TRAD),
 r("姐在房中", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("心中自有小百灵", U, urls=GANNAN, notes="Labelled 赣南民歌, but it may be a newer song; no authorship found."),
 r("打支山歌过横排", T, urls=XINGGUO + " ; https://tv.cctv.cn/2021/12/26/VIDEesQpgeuCbiptz8yPJIO6211226.shtml", notes="兴国山歌. No song-level date."),
 r("打鞋底", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("斑鸠调", T, urls=GANNAN, notes="赣南采茶戏 tune (黄玉英; 吴碧霞). No song-level date."),
 r("映山红", NC, "1970s", "1974", "Song in the film 《闪闪的红星》, released 1974", "傅庚辰 (music); 陆柱国 (lyrics)", "1973", "https://zh.wikipedia.org/zh-hans/%E6%98%A0%E5%B1%B1%E7%BA%A2_(%E6%AD%8C%E6%9B%B2) ; https://baike.baidu.com/item/%E6%98%A0%E5%B1%B1%E7%BA%A2/1056830", "high", "Written in the Jiangxi folk style."),
 r("武宁打鼓歌", T, "Qing (Qianlong, per 非遗 description)", urls="https://www.ihchina.cn/project_details/12455/", conf="low", notes="薅草锣鼓 said to have formed in the Qianlong era from Hubei 薅草歌 (heritage description, undocumented). National 非遗 2008."),
 r("江西传统民歌（龙虎山船家）", T, notes="Field recording; piece not identified."),
 r("江西童谣", NC, "Republican (1930s)", NA, "百代 (Pathé) 78rpm disc sung by 胡蓉蓉 (1930s)", "金钢 (黎锦光)", NA, "https://www.kongfz.cn/72767952/pic/", "medium", "A 1930s Shanghai children's song in folk style, not a Jiangxi field song. The exact year was not found."),
 r("照镜子", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("牡丹调", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("瓜子仁", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("睄妹子", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("红绣鞋", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("萍乡童谣", U, notes="Provenance uncertain (flagged in curation)."),
 r("请茶歌", NC, "1950s", "1958", "Composed 1958 (lyrics written May 1957 in 吉安)", "文莽彦 (lyrics); 解策励 (music)", "1957-1958", "https://zh.wikipedia.org/zh-hans/%E8%AF%B7%E8%8C%B6%E6%AD%8C ; https://www.thepaper.cn/newsDetail_forward_13935478", "high", ""),
 r("送表哥", T, urls=GANNAN, notes="赣南采茶调. No song-level date."),
 r("送郎调", T, NA, "1960", "Collected by 朱正本 et al. (空政文工团) in 1960 Jiangxi fieldwork as 《长歌》/《送郎调》", urls=SONGLANG, conf="medium", notes="赣南采茶戏 melody and the source tune of 十送红军."),
 r("长歌（送郎调）", T, NA, "1960", "Collected by 朱正本 et al. in 1960 Jiangxi fieldwork as 《长歌》/《送郎调》", urls=SONGLANG, conf="medium", notes="Same tune as 送郎调."),
 r("长铜钱歌", T, urls=GANNAN, notes="赣南民歌 (黄玉英). No song-level date."),
 r("闹五更", T, urls=GANNAN, notes="赣南民歌 (黄玉英). 五更调 is a widespread 小调 type. No song-level date."),
 r("青草小河边", TA, NA, NA, NA, "吴颂今 (credited producer/arranger)", "2000", "https://music.apple.com/cn/song/%E9%9D%92%E8%8D%89%E5%B0%8F%E6%B2%B3%E8%BE%B9-%E6%B1%9F%E8%A5%BF%E7%89%A7%E7%AB%A5%E5%B1%B1%E6%AD%8C/1606425924", "low", "Children's-choir release (颂今童歌会, 2000) labelled 江西牧童山歌. The underlying traditional tune was not verified."),
],
}

for region, rows in DATA.items():
    with open(os.path.join(OUT, f"{region}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for row in rows:
            row = dict(row, region=region)
            w.writerow({c: row[c] for c in COLS})
print("done")
