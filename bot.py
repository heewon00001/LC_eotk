"""
림버스 컴퍼니 대사 검색 디스코드 봇
- /대사검색 : 스토리 대사 검색
- /설명검색 : 인격/스킬/EGO 등 설명 검색
"""

import os
import random
import re
import discord
from discord import app_commands
from discord.ext import commands
import json
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
MISC_DIR       = BASE_DIR / "Misc_KRjson"
# ──────────────────────────────────────────

RESULTS_PER_PAGE = 5

FOOTER_MESSAGES = [
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
    "저도 언젠가는 잘 할 수 있을 거예요. ",

    "오, 찾았어? 잘됐네~ 근데 밥은 언제 먹어?",
    "대사 찾으면서 밥 생각이 나는 건 왜일까..",
    "간식 줘.",

    "결과가 없다면 다시 검색하도록.",
    "쓸데없는 검색에 시간 낭비하지 말도록.",
    
    "찾는 게 있으면 제대로 검색하세요.",
    "..이 벌레는 계속 이상한 소리나 낸다구요. 아무튼 대사는 찾았네요.",

    "..어이, 담배 좀 빌릴 수 있나? \n이곳은 금연구역이라네.",
    "집에가고파",

]

MAIN_CHAPTERS  = {"1","2","3","4","5","6","7","8","9"}
INTER_CHAPTERS = {"3.5","4.5","5.5","6.5","7.5","8.5","9.5"}

search_data: List[Dict] = []
misc_data:   List[Dict] = []


# ── 챕터 추출 ────────────────────────────────
def get_chapter(key: str) -> str:
    m = re.match(r'^(\d+)D', key)
    if m: return m.group(1)
    m = re.match(r'^S(\d)', key)
    if m: return m.group(1)
    return "0"

def get_dtale_chapter(key: str) -> str:
    m = re.match(r'^E([1-9])\d\d', key)
    if m: return f"{m.group(1)}.5"
    return "기타"

def get_misc_category(key: str) -> str:
    if re.match(r'^Announcer', key):       return "어나운서"
    if re.match(r'^AbDlg', key):           return "이상현상대사"
    if re.match(r'^Skills_(personality|Ego)', key): return "스킬설명"
    if re.match(r'^Passives?', key):       return "패시브"
    if re.match(r'^Egos', key):            return "EGO"
    if re.match(r'^BattleSpeechBubble', key): return "배틀대사"
    if re.match(r'^BgmLyrics', key):       return "BGM가사"
    if re.match(r'^StoryTheaterDanteNote', key): return "단테노트"
    return "기타"


# ── 스토리 데이터 로드 ───────────────────────
def load_all_data():
    search_data.clear()
    for kr_file in sorted(KR_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]
        _load_story_file(kr_file, VOICE_DIR / f"{key}.json", key, get_chapter(key))
    for kr_file in sorted(DTALE_KR_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]
        _load_story_file(kr_file, DTALE_V_DIR / f"{key}.json", key, get_dtale_chapter(key))
    print(f"[봇] 스토리 {len(search_data)}개 대사 로드 완료")

def _load_story_file(kr_file: Path, voice_file: Path, key: str, chapter: str):
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


# -- Misc 데이터 로드 --
def load_misc_data():
    misc_data.clear()
    for kr_file in sorted(MISC_DIR.glob("KR_*.json")):
        key = kr_file.stem[3:]
        category = get_misc_category(key)
        try:
            with open(kr_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[경고] {kr_file.name} 로드 실패: {e}")
            continue
        if "dataList" not in data:
            continue
        for item in data["dataList"]:
            if "id" not in item:
                continue
            for entry in _extract_misc_entries(item, category, key):
                misc_data.append(entry)
    print(f"[봇] Misc {len(misc_data)}개 항목 로드 완료")

def _extract_misc_entries(item, category, scene):
    vid = item["id"]
    base = {"scene": scene, "category": category, "id": vid}
    if category == "스킬설명":
        lvs = item.get("levelList", [])
        if not lvs: return []
        last = lvs[-1]
        name = last.get("name", "")
        desc = last.get("desc", "")
        text = (name + ": " + desc) if name and desc else (name or desc)
        if not text: return []
        return [{**base, "speaker": "", "content": text, "extra": name}]
    if category in ("패시브", "EGO"):
        name = item.get("name", "")
        desc = item.get("desc", "")
        text = (name + ": " + desc) if name and desc else (name or desc)
        if not text: return []
        return [{**base, "speaker": "", "content": text, "extra": name}]
    if category == "이상현상대사":
        dialog = item.get("dialog", "")
        if not dialog: return []
        return [{**base, "speaker": item.get("teller", ""), "content": dialog, "extra": ""}]
    if category in ("어나운서", "배틀대사"):
        text = item.get("dlg", "") or item.get("desc", "")
        if not text: return []
        return [{**base, "speaker": "", "content": text, "extra": ""}]
    text = str(item.get("content") or item.get("dlg") or item.get("dialog") or item.get("desc") or "")
    if not text: return []
    return [{**base, "speaker": "", "content": text, "extra": ""}]

def do_search(keyword, filter_val, speaker):
    results = []
    kw = keyword.lower() if keyword else None
    sp = speaker.lower() if speaker else None
    for entry in search_data:
        if filter_val:
            c = entry["chapter"]
            if filter_val == "main_all" and c not in MAIN_CHAPTERS: continue
            elif filter_val == "inter_all" and c not in INTER_CHAPTERS: continue
            elif filter_val == "기타" and c != "기타": continue
            elif filter_val not in ("main_all", "inter_all", "기타") and c != filter_val: continue
        if sp and sp not in entry["model"].lower(): continue
        if kw and kw not in entry["content"].lower(): continue
        results.append(entry)
    return results

def do_misc_search(keyword, category):
    results = []
    kw = keyword.lower() if keyword else None
    for entry in misc_data:
        if category and category != "all" and entry["category"] != category: continue
        if kw and kw not in entry["content"].lower(): continue
        results.append(entry)
    return results
