"""
림버스 컴퍼니 대사 검색 디스코드 봇
- /대사검색 키워드:[text] 장:[선택] 으로 사용
- 대사 + 음성파일명 같이 출력
- 이전/다음 버튼으로 페이지네이션
"""

import os
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
BASE_DIR  = Path(__file__).parent        # bot.py 있는 폴더 기준
KR_DIR    = BASE_DIR / "KR_json"         # 대사 텍스트 json 폴더
VOICE_DIR = BASE_DIR / "json"            # 음성파일 정보 json 폴더
# ──────────────────────────────────────────

RESULTS_PER_PAGE = 5

# 전체 대사 데이터 저장소
search_data: List[Dict] = []


def get_chapter(key: str) -> str:
    """파일명에서 장 번호 추출
    - 1D101A  → "1"   (1~8장 형식)
    - S901B   → "9"   (9장 형식)
    """
    m = re.match(r'^(\d+)D', key)       # 1D, 8D 등
    if m:
        return m.group(1)
    m = re.match(r'^S(\d)', key)        # S9...
    if m:
        return m.group(1)
    return "0"


# ── 데이터 로드 ──────────────────────────────
def load_all_data():
    """봇 시작 시 모든 json을 메모리에 로드"""
    for kr_file in sorted(KR_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]   # "KR_1D101A" → "1D101A", "KR_S901B" → "S901B"
        chapter = get_chapter(key)

        # ── KR json 로드
        try:
            with open(kr_file, encoding="utf-8") as f:
                kr_list = json.load(f)["dataList"]
        except Exception as e:
            print(f"[경고] {kr_file.name} 로드 실패: {e}")
            continue

        # ── 음성 json 로드 (없으면 빈 dict)
        voice_file = VOICE_DIR / f"{key}.json"
        voice_map: Dict = {}
        if voice_file.exists():
            try:
                with open(voice_file, encoding="utf-8") as f:
                    voice_list = json.load(f)["dataList"]
                voice_map = {item["id"]: item for item in voice_list if "id" in item}
            except Exception as e:
                print(f"[경고] {voice_file.name} 로드 실패: {e}")

        # ── 두 json을 id 기준으로 합쳐서 저장
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

    print(f"[봇] {len(search_data)}개 대사 로드 완료")


def do_search(keyword: str, chapter: Optional[str]) -> List[Dict]:
    """키워드 + 장 필터로 대사 검색"""
    results = []
    kw = keyword.lower()
    for entry in search_data:
        if chapter and entry["chapter"] != chapter:
            continue
        if kw in entry["content"].lower():
            results.append(entry)
    return results


# ── 페이지네이션 UI ──────────────────────────
class SearchView(discord.ui.View):
    def __init__(self, results: List[Dict], keyword: str, chapter_label: str):
        super().__init__(timeout=180)
        self.results       = results
        self.keyword       = keyword
        self.chapter_label = chapter_label
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

        embed = discord.Embed(
            title="🔍 림버스 컴퍼니 대사 검색",
            description=(
                f"**키워드:** `{self.keyword}`　"
                f"**장:** {self.chapter_label}　"
                f"**{len(self.results)}개 결과** "
                f"({self.page + 1} / {self.max_page + 1} 페이지)"
            ),
            color=0xE4444F
        )

        for r in page_results:
            model = r["model"] if r["model"] else "내레이션"
            voice = f"`{r['voice']}`" if r["voice"] else "❌ 없음"
            place_str = f"\n📍 _{r['place']}_" if r["place"] else ""

            embed.add_field(
                name=f"[{r['scene']}] {model}",
                value=f"{r['content']}{place_str}\n🔊 음성: {voice}",
                inline=False
            )

        embed.set_footer(text="림버스 컴퍼니 대사 검색봇")
        return embed

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


# ── 봇 설정 ─────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    load_all_data()
    await bot.tree.sync()
    print(f"[봇] 로그인 완료: {bot.user} (ID: {bot.user.id})")
    print("[봇] 슬래시 커맨드 동기화 완료")


@bot.tree.command(name="대사검색", description="림버스 컴퍼니 대사를 검색합니다")
@app_commands.describe(
    키워드="검색할 단어 또는 문장 (예: 홍원에 필요한)",
    장="칸토 번호 (예: 1, 2, 8 … 비워두면 전체 검색)"
)
async def search_command(
    interaction: discord.Interaction,
    키워드: str,
    장: Optional[int] = None
):
    await interaction.response.defer()

    chapter_str   = str(장) if 장 is not None else None
    chapter_label = f"{장}장" if 장 is not None else "전체"

    results = do_search(키워드, chapter_str)

    if not results:
        await interaction.followup.send(
            f"❌ `{키워드}` 에 해당하는 대사가 없습니다. (장: {chapter_label})"
        )
        return

    view  = SearchView(results, 키워드, chapter_label)
    embed = view.make_embed()
    await interaction.followup.send(embed=embed, view=view)


# ── 실행 ─────────────────────────────────────
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        raise ValueError("[봇] .env 파일에 TOKEN이 없습니다!")
    bot.run(token)
