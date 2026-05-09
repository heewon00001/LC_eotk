"""
림버스 컴퍼니 대사 검색 디스코드 봇
- /대사검색 키워드:[선택] 화자:[선택] 장:[선택] 으로 사용
- 대사 + 음성파일명 같이 출력
- 이전/다음 버튼으로 페이지네이션
"""

import os
import random
import discord
from discord import app_commands
from discord.ext import commands
import json
import re
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
KR_DIR         = BASE_DIR / "KR_json"
VOICE_DIR      = BASE_DIR / "json"
DTALE_KR_DIR   = BASE_DIR / "Dtales_KRjson"
DTALE_V_DIR    = BASE_DIR / "Dtales_json"
# ──────────────────────────────────────────

RESULTS_PER_PAGE = 5

FOOTER_MESSAGES = [
    # "과연 이런걸 보러 올 사람이 있을까 ㅋㅋ"
    # "대사 꼬라지가 말이 아니라고요? 시ㅣㅣ바 램호엔이 좋은걸 어카라고 샤ㅑ갈ㄹㄹ"
    # "시ㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣ바",
    # 개현타오네
    "제작자(히원)의 최애는 호엔하임이라네요(9장)",
    "제작자(히원)의 최애는 호엔하임이라네요(9장)",
    "제작자(히원)의 최애는 호엔하임이라네요(9장)",
    "제작자(히원)의 최애는 호엔하임이라네요(9장)",
    "제작자(히원)의 최애는 호엔하임이라네요(9장)",
    "림버스 컴퍼니의 수석 연구원 호엔하임(이 키우는 벌레)이네.",
    "두루지벌레가 대사를 찾는 중이군",
    "집가고싶다",
    "추가하고싶은 대사 / 기능이 있다면 히원의 dm으로",
    "봇이 두루지벌레인 이유는 호엔하임을 닮아서라고..",
    "놀랍게도 이 봇에는 이스터에그가 있다네",
    "음성파일은 구드에서 검색할 수 있다네",
    "팀장님 저 벌레는 어디서 데려온거에요",
    "흠..",
    "아아. 마이크 테스트.",
    "130",
    "아름다운.. 대사군요",
    "팀장님? 언제 벌레가 되신거죠..?\n..나는 여기 있네만",
    "알리사.. 에프킬라 저리 치우게",
    "두루지벌레의 영문명은 blipbug라네",
    "뭐..놀랍군. 벌레가 이정도의 지능을 가질 줄이야.",
    "오, 이 대사 나도 좋아하는데.",
    "기다리게. 지금 불러오는 중이니.",
    "*어딘가에서 알리사가 에프킬라를 꺼내 드는 소리가 들린다.*",
    "이 대사의 의미를 반추해보게.",
    
    "검색이 되었구료.",
    "..이 대사가 맞는가.",
    "이상적인 대사구료.",
    "이상적인 벌레구료",
    
    "파우스트는 이 대사를 알고 있어요.",
    "검색 결과를 분석 중이에요. 잠깐만요.",
    "파우스트는 모든 대사를 알고 있어요.",
    
    "정의의 해결사는 대사도 빠르게 찾는다네!",
    "마땅한 대사를 찾아내는 것이야말로, 정의로운 해결사의 덕목이라네!",
    "불가능한 꿈이라 할지라도, 찾아내고야 말겠노라!",
    "대사 검색에서 포기란 없는 법이라네!",

    "찾던 대사가 나왔군요. 잘 쓰시길.",
    "모든 것은 찰나에 불과하지만.. 대사는 남아있네요.",
    "이런 대사도 있었군요? 흥미롭네요~",
    
    "찾.완. 꺼져.",
    "벌.대.",

    "찾는 대사가 이거냐?",
    "이 벌레는 아까부터 뭐라는거야? ..조수?",

    "저... 찾으시는 대사가 맞나요..?",
    "이 벌레는 생각보다 쓸모가 많아요. 아마도요..?",
    "저도 언젠가는 잘 할 수 있을 거예요.",

    "오, 찾았어? 잘됐네~ 근데 밥은 언제 먹어?",
    "대사 찾으면서 밥 생각이 나는 건 왜일까..",
    "간식 줘.",

    "결과가 없다면 다시 검색하도록.",
    "쓸데없는 검색에 시간 낭비하지 말도록.",
    
    "찾는 게 있으면 제대로 검색하세요.",
    "..이 벌레는 계속 이상한 소리나 낸다구요. 아무튼 대사는 찾았네요.",

    "..어이, 담배 좀 빌릴 수 있나? \n이곳은 금연구역이라네.",
    "신기한 벌레구만.",

]

""
MAIN_CHAPTERS  = {"1","2","3","4","5","6","7","8","9"}
INTER_CHAPTERS = {"3.5","4.5","5.5","6.5","7.5","8.5","9.5"}

search_data: List[Dict] = []


def get_chapter(key: str) -> str:
    m = re.match(r'^(\d+)D', key)
    if m:
        return m.group(1)
    m = re.match(r'^S(\d)', key)
    if m:
        return m.group(1)
    return "0"


def get_dtale_chapter(key: str) -> str:
    m = re.match(r'^E([1-9])\d\d', key)
    if m:
        return f"{m.group(1)}.5"
    return "기타"


def load_all_data():
    search_data.clear()
    for kr_file in sorted(KR_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]
        _load_file(kr_file, VOICE_DIR / f"{key}.json", key, get_chapter(key))

    for kr_file in sorted(DTALE_KR_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]
        _load_file(kr_file, DTALE_V_DIR / f"{key}.json", key, get_dtale_chapter(key))

    print(f"[봇] {len(search_data)}개 대사 로드 완료")


def _load_file(kr_file: Path, voice_file: Path, key: str, chapter: str):
    try:
        with open(kr_file, encoding="utf-8") as f:
            kr_list = json.load(f)["dataList"]
    except Exception as e:
        print(f"[경고] {kr_file.name} 로드 실패: {e}")
        return

    voice_map: Dict = {}
    if voice_file.exists():
        try:
            with open(voice_file, encoding="utf-8") as f:
                voice_list = json.load(f)["dataList"]
            voice_map = {item["id"]: item for item in voice_list if "id" in item}
        except Exception as e:
            print(f"[경고] {voice_file.name} 로드 실패: {e}")

    for item in kr_list:
        if "id" not in item or "content" not in item:
            continue
        vid = item["id"]
        voice_entry = voice_map.get(vid, {})
        search_data.append({
            "scene":   key,
            "chapter": chapter,
            "id":      vid,
            "model":   item.get("model", ""),
            "content": item["content"],
            "place":   item.get("place", ""),
            "voice":   voice_entry.get("voice", "")
        })


def do_search(keyword: Optional[str], filter_val: Optional[str], speaker: Optional[str]) -> List[Dict]:
    results = []
    kw = keyword.lower() if keyword else None
    sp = speaker.lower() if speaker else None
    for entry in search_data:
        if filter_val:
            c = entry["chapter"]
            if filter_val == "main_all" and c not in MAIN_CHAPTERS:
                continue
            elif filter_val == "inter_all" and c not in INTER_CHAPTERS:
                continue
            elif filter_val == "기타" and c != "기타":
                continue
            elif filter_val not in ("main_all", "inter_all", "기타") and c != filter_val:
                continue
        if sp and sp not in entry["model"].lower():
            continue
        if kw and kw not in entry["content"].lower():
            continue
        results.append(entry)
    return results



# ── 페이지 이동 Modal ────────────────────────
class GotoPageModal(discord.ui.Modal, title="페이지 이동"):
    page_num = discord.ui.TextInput(
        label="이동할 페이지 번호",
        placeholder="숫자 입력.",
        min_length=1,
        max_length=5,
    )

    def __init__(self, view: "SearchView"):
        super().__init__()
        self.search_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target = int(self.page_num.value) - 1
            if target < 0 or target > self.search_view.max_page:
                await interaction.response.send_message(
                    f"1 ~ {self.search_view.max_page + 1} 사이의 숫자를 입력하게..", ephemeral=True
                )
                return
            self.search_view.page = target
            self.search_view._update_buttons()
            await interaction.response.edit_message(embed=self.search_view.make_embed(), view=self.search_view)
        except ValueError:
            await interaction.response.send_message("숫자만 입력하게.", ephemeral=True)
# ── 페이지네이션 UI ──────────────────────────
class SearchView(discord.ui.View):
    def __init__(self, results: List[Dict], keyword: Optional[str], chapter_label: str, speaker: Optional[str]):
        super().__init__(timeout=180)
        self.results       = results
        self.keyword       = keyword
        self.chapter_label = chapter_label
        self.speaker       = speaker
        self.page          = 0
        self.max_page      = (len(results) - 1) // RESULTS_PER_PAGE
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = (self.page == 0)
        self.next_btn.disabled = (self.page == self.max_page)

    def make_embed(self) -> discord.Embed:
        start = self.page * RESULTS_PER_PAGE
        end   = start + RESULTS_PER_PAGE
        page_results = self.results[start:end]

        kw_str      = f"**키워드:** `{self.keyword}`　" if self.keyword else ""
        speaker_str = f"**화자:** `{self.speaker}`　"  if self.speaker else ""
        embed = discord.Embed(
            title="🔍 림버스 컴퍼니 대사 검색",
            description=(
                f"{kw_str}"
                f"{speaker_str}"
                f"**장:** {self.chapter_label}　"
                f"**{len(self.results)}개 결과** "
                f"({self.page + 1} / {self.max_page + 1} 페이지)"
            ),
            color=0xE4444F
        )

        for r in page_results:
            model = r["model"] if r["model"] else "내레이션"
            voice = f"`{r['voice']}`" if r["voice"] else "없음"
            place_str = f"\n📍 _{r['place']}_" if r["place"] else ""

            embed.add_field(
                name=f"[{r['scene']}] {model}",
                value=f"{r['content']}{place_str}\n🔊 음성: {voice}",
                inline=False
            )

        embed.set_footer(text=random.choice(FOOTER_MESSAGES))
        return embed

    @discord.ui.button(label="페이지 이동", style=discord.ButtonStyle.primary)
    async def goto_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GotoPageModal(self))

    @discord.ui.button(label="◀ 이전", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="다음 ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    load_all_data()
    await bot.tree.sync()
    print(f"[봇] 로그인 완료: {bot.user} (ID: {bot.user.id})")
    print("[봇] 슬래시 커맨드 동기화 완료")


@bot.tree.command(name="대사검색", description="림버스 컴퍼니 대사를 검색하게.")
@app_commands.describe(
    키워드="검색할 단어 또는 문장 ",
    화자="캐릭터 이름 (예: 호엔하임, 단테)",
    장="검색 범위 "
)
@app_commands.choices(장=[
    app_commands.Choice(name="전체",              value="all"),
    app_commands.Choice(name="메인스토리 전체",   value="main_all"),
    app_commands.Choice(name="1장",               value="1"),
    app_commands.Choice(name="2장",               value="2"),
    app_commands.Choice(name="3장",               value="3"),
    app_commands.Choice(name="4장",               value="4"),
    app_commands.Choice(name="5장",               value="5"),
    app_commands.Choice(name="6장",               value="6"),
    app_commands.Choice(name="7장",               value="7"),
    app_commands.Choice(name="8장",               value="8"),
    app_commands.Choice(name="9장",               value="9"),
    app_commands.Choice(name="인터발로 전체",     value="inter_all"),
    app_commands.Choice(name="3.5장 헬스 치킨",   value="3.5"),
    app_commands.Choice(name="4.5장 우.미.다",    value="4.5"),
    app_commands.Choice(name="5.5장",             value="5.5"),
    app_commands.Choice(name="6.5장",             value="6.5"),
    app_commands.Choice(name="7.5장",             value="7.5"),
    app_commands.Choice(name="8.5장",             value="8.5"),
    app_commands.Choice(name="9.5장",             value="9.5"),
    app_commands.Choice(name="기타 전체 (미니스토리/발푸밤 등)", value="기타"),
])
async def search_command(
    interaction: discord.Interaction,
    키워드: Optional[str] = None,
    화자: Optional[str] = None,
    장: Optional[app_commands.Choice[str]] = None,
):
    await interaction.response.defer()

    if not 키워드 and not 화자 and not 장:
        await interaction.followup.send(
            "...적어도 키워드, 화자, 장 중 하나 이상은 입력해야 하네.", ephemeral=True
        )
        return

    if 장 is None or 장.value == "all":
        filter_val    = None
        chapter_label = "전체"
    else:
        filter_val    = 장.value
        chapter_label = 장.name

    results = do_search(키워드, filter_val, 화자)

    if not results:
        parts = []
        if 키워드: parts.append(f"키워드: {키워드}")
        if 화자:   parts.append(f"화자: {화자}")
        parts.append(f"장: {chapter_label}")
        await interaction.followup.send(
            f"{' / '.join(parts)} — 해당하는 대사를 찾지 못했네."
        )
        return

    view  = SearchView(results, 키워드, chapter_label, 화자)
    embed = view.make_embed()
    await interaction.followup.send(embed=embed, view=view)


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        raise ValueError(".env 파일에 TOKEN이 없네. 다시 확인해보게나")
    bot.run(token)


