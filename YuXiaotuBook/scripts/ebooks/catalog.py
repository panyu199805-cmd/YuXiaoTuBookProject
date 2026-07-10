"""全站书籍电子书解读目录（版式与《非暴力沟通》一致）。"""
from __future__ import annotations

from ebooks.fei_bao_li_gou_tong import EBOOK_BODY, EBOOK_CONTENT as FEI_BAO_LI_CONTENT

# 各书导读标题（正文沿用非暴力沟通同款结构与篇幅）
BOOK_EBOOK_TITLES: dict[str, str] = {
    "被讨厌的勇气": "读懂《被讨厌的勇气》：自由，就是被别人讨厌",
    "小王子": "读懂《小王子》：真正重要的，眼睛看不见",
    "非暴力沟通": "读懂《非暴力沟通》：好好说话，不是忍让，是自救",
    "原则": "读懂《原则》：用原则对抗人生的不确定",
    "活着": "读懂《活着》：在苦难里，依然热烈地活",
    "正面管教": "读懂《正面管教》：和善而坚定地陪伴孩子",
    "心流": "读懂《心流》：全神贯注时，幸福自然发生",
    "解忧杂货店": "读懂《解忧杂货店》：每个烦恼都值得被温柔接住",
    "深度工作": "读懂《深度工作》：专注，是稀缺时代的超能力",
    "我们仨": "读懂《我们仨》：一家人，最无悔的相守",
}

from book_video_asset import BOOK_INTRO_VIDEO_URL

DEFAULT_VIDEO_URL = BOOK_INTRO_VIDEO_URL


def ebook_content_for(title: str) -> str:
    if title == "非暴力沟通":
        return FEI_BAO_LI_CONTENT
    heading = BOOK_EBOOK_TITLES.get(title, f"读懂《{title}》：在阅读里遇见更好的自己")
    return f"{heading}\n---\n{EBOOK_BODY}"


ALL_EBOOK_TITLES = list(BOOK_EBOOK_TITLES.keys())
