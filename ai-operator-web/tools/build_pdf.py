#!/usr/bin/env python3
"""Generuje private/15-promptu-ai-operator.pdf (lead magnet). Spuštění: npm run pdf"""
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "private" / "15-promptu-ai-operator.pdf"
FONTS = Path("/usr/share/fonts/truetype/dejavu")

pdfmetrics.registerFont(TTFont("Sans", FONTS / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", FONTS / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONTS / "DejaVuSansMono.ttf"))

INK, TEXT, MUTED = HexColor("#14213D"), HexColor("#243047"), HexColor("#5B6475")
COBALT, SHEET, LINE = HexColor("#2F5BEA"), HexColor("#EEF1F6"), HexColor("#D6DCE6")

S = {
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=26, leading=30, textColor=INK, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=12.5, leading=16, textColor=INK, spaceBefore=4, spaceAfter=3),
    "lead": ParagraphStyle("lead", fontName="Sans", fontSize=12, leading=17, textColor=TEXT, spaceAfter=8),
    "p": ParagraphStyle("p", fontName="Sans", fontSize=9.2, leading=13, textColor=TEXT, spaceAfter=4),
    "use": ParagraphStyle("use", fontName="Sans", fontSize=8.6, leading=12, textColor=MUTED, spaceAfter=4),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=7.7, leading=10.4, textColor=INK, alignment=TA_LEFT),
}

PROMPTS = [
    ("Čistý název produktu z feedu dodavatele",
     "Když feed přijde VELKÝMI PÍSMENY, bez diakritiky a se zkratkami.",
     """Jsi produktový editor českého e-shopu. Z údajů dodavatele vytvoř název produktu.
Pravidla:
- Struktura: [Typ produktu] [značka/model] – [2–3 klíčové parametry]
- Česká diakritika, první písmeno velké, zbytek podle pravopisu
- Jednotky s mezerou: 40 W, 600 × 600 mm, 4000 K
- Max. 80 znaků, žádné vykřičníky ani marketingové výrazy
- Používej POUZE údaje ze vstupu. Nic nedoplňuj.
Vstup: {RADEK_Z_FEEDU}
Výstup: pouze název, jeden řádek."""),
    ("Krátký popis do výpisu kategorie",
     "Perex pod název v kategorii a ve srovnávačích (Heureka, Zboží).",
     """Napiš krátký popis produktu pro výpis kategorie e-shopu.
- 1–2 věty, max. 200 znaků
- První věta: k čemu produkt je a pro koho
- Druhá věta: hlavní praktický přínos (montáž, úspora, kompatibilita)
- Vykání, věcný tón, bez superlativů („nejlepší“, „revoluční“)
- Parametry jen ze vstupu; pokud údaj chybí, nevymýšlej ho
Produkt: {NAZEV}
Data: {PARAMETRY_A_POPIS_DODAVATELE}"""),
    ("Dlouhý popis v HTML se strukturou",
     "Hlavní popis produktu, který jde rovnou do editoru Shoptetu.",
     """Vytvoř dlouhý popis produktu v čistém HTML pro Shoptet.
Struktura:
<p> úvod 2–3 věty: použití a cílový zákazník </p>
<h3>Hlavní výhody</h3><ul> 3–5 bodů, každý = parametr + přínos </ul>
<h3>Použití</h3><p> kde a jak se produkt používá </p>
<h3>Obsah balení</h3><ul> jen pokud je ve vstupu </ul>
Pravidla: povolené tagy p, h3, ul, li, strong. Žádné styly, žádné emoji.
Pokud informace chybí, sekci vynech. Nic si nedomýšlej.
Data: {DATA_DODAVATELE}"""),
    ("Tabulka parametrů z chaotického textu",
     "Když dodavatel posílá parametry v jednom odstavci nebo v PDF.",
     """Z textu vytáhni technické parametry do tabulky.
Výstup: CSV se sloupci parametr;hodnota;jednotka
- Názvy parametrů podle tohoto seznamu: {SEZNAM_PARAMETRU_ESHOPU}
- Hodnotu bez jednotky, desetinná čárka, jednotka zvlášť
- Parametr, který v textu není, NEUVÁDĚJ
- Na konec přidej řádek „NEJASNE;…“ se vším, co nešlo jednoznačně zařadit
Text: {TEXT_DODAVATELE}"""),
    ("SEO title a meta description",
     "Pro detail produktu i kategorii. Výsledek kontroluj v náhledu výsledků Googlu.",
     """Napiš SEO title a meta description pro stránku produktu.
- Title: max. 60 znaků, klíčové slovo na začátku, na konci „| {NAZEV_ESHOPU}“
- Description: 140–155 znaků, přínos + parametr + výzva (např. „Skladem, odeslání do 24 h.“)
- Klíčové slovo: {HLAVNI_KLICOVE_SLOVO}
- Žádná tvrzení o ceně, dopravě ani skladu, která nejsou ve vstupu
Produkt: {NAZEV}
Popis: {KRATKY_POPIS}
Výstup: dva řádky, TITLE: … a DESCRIPTION: …"""),
    ("Překlad do slovenštiny s glosářem",
     "Pro .sk mutaci e-shopu. Glosář drží terminologii napříč katalogem.",
     """Přelož text produktu z češtiny do spisovné slovenštiny pro e-shop.
Glosář (vždy použij tyto překlady):
{GLOSAR — např. svítidlo = svietidlo; podhled = podhľad; zdroj = zdroj}
Pravidla:
- Zachovej HTML tagy, čísla, jednotky a kódy produktů beze změny
- Vykání, přirozený slovenský slovosled, žádné bohemismy
- Značky a názvy modelů nepřekládej
Text: {CESKY_TEXT}"""),
    ("Překlad do polštiny pro Allegro",
     "Allegro má vlastní logiku názvů: délka 75 znaků a vyhledávací slova.",
     """Připrav nabídku pro Allegro v polštině.
1) Název: max. 75 znaků, začni typem produktu, pak parametry, které
   Poláci hledají (rozměr, výkon, barva). Bez velkých písmen a symbolů.
2) Popis: přelož český popis, zachovej strukturu a HTML.
3) Parametry: přelož názvy parametrů podle kategorie Allegro {KATEGORIE}.
Nic nepřidávej, žádné sliby dopravy a záruky, které nejsou ve vstupu.
Vstup: {NAZEV} / {POPIS} / {PARAMETRY}"""),
    ("Kontrola kvality překladu",
     "Druhé kolo: jiný chat nebo jiný model kontroluje první výstup.",
     """Jsi rodilý mluvčí jazyka {JAZYK} a korektor e-shopových textů.
Porovnej originál a překlad. Vypiš tabulku: úsek | problém | návrh opravy.
Kontroluj: 1) posun významu, 2) změněná čísla/jednotky/kódy,
3) chybějící nebo přidané informace, 4) nepřirozené formulace,
5) nekonzistenci s glosářem: {GLOSAR}.
Pokud je vše v pořádku, napiš jen „OK“.
Originál: {CS}
Překlad: {PREKLAD}"""),
    ("Popis kategorie pro SEO",
     "Text nad nebo pod výpisem kategorie. Pomáhá s longtail dotazy.",
     """Napiš text kategorie „{KATEGORIE}“ pro e-shop.
- 150–250 slov, 2–3 odstavce, jeden podnadpis <h2>
- Odpověz na otázky, které si zákazník klade před nákupem:
  jak vybrat, na jaké parametry se dívat, pro koho je co vhodné
- Přirozeně použij výrazy: {KLICOVA_SLOVA}
- Žádné konkrétní ceny ani značky, které nejsou ve vstupu
Sortiment v kategorii: {PREHLED_PRODUKTU}"""),
    ("FAQ z dotazů zákazníků",
     "Vlož reálné dotazy z e-mailů, chatu nebo Heureky.",
     """Z dotazů zákazníků vytvoř FAQ k produktu.
- Seskup podobné dotazy, max. 6 otázek
- Otázka tak, jak by ji napsal zákazník; odpověď 1–3 věty
- Odpovídej POUZE z dat produktu. Když odpověď v datech není,
  napiš „DOPLNIT: …“ a co je potřeba zjistit
Výstup: HTML <h3>otázka</h3><p>odpověď</p>
Dotazy: {DOTAZY}
Data produktu: {DATA}"""),
    ("Srovnání variant produktu",
     "Pomáhá zákazníkovi vybrat variantu a snižuje počet vratek.",
     """Porovnej varianty produktu v tabulce pro e-shop.
- Řádky = parametry, které se mezi variantami liší (stejné vynech)
- Pod tabulku napiš „Kterou vybrat“: 1 věta na variantu, pro jaké použití
- HTML: <table> se záhlavím, bez stylů
- Pouze údaje ze vstupu
Varianty: {VARIANTY_S_PARAMETRY}"""),
    ("Alt texty obrázků",
     "Přístupnost a obrázkové vyhledávání. Hromadně pro celou galerii.",
     """Napiš alt texty k obrázkům produktu {NAZEV}.
- Max. 120 znaků, popiš co je na obrázku (detail, v interiéru, balení)
- Začni typem produktu, nepoužívej „obrázek“ ani „foto“
- Žádné vycpávání klíčovými slovy
Výstup: soubor;alt
Obrázky: {SEZNAM_SOUBORU_A_POPIS_CO_NA_NICH_JE}"""),
    ("Sjednocení tónu v celém katalogu",
     "Když popisy psalo víc lidí a každý jinak.",
     """Přepiš popis tak, aby odpovídal stylu našeho e-shopu.
Styl: {PRAVIDLA — např. vykání, krátké věty, nejdřív použití, pak parametry,
bez superlativů, jednotky s mezerou, „dodáváme“ místo „nabízíme“}
Vzorový popis v našem stylu: {VZOR}
- Zachovej všechny fakty a parametry, nic nepřidávej ani neubírej
- Zachovej HTML strukturu
Popis k úpravě: {POPIS}"""),
    ("Hromadné zpracování přes CSV",
     "Desítky produktů najednou. Export z Shoptetu/BaseLinkeru → AI → import.",
     """Dostaneš CSV (oddělovač ;) se sloupci: kod;nazev_dodavatele;data.
Pro KAŽDÝ řádek vytvoř: kod;nazev;kratky_popis
- nazev podle pravidel: {PRAVIDLA_Z_PROMPTU_1}
- kratky_popis podle pravidel: {PRAVIDLA_Z_PROMPTU_2}
- Zachovej pořadí a kódy, nevynechávej řádky
- Středník v textu nahraď čárkou, výstup bez uvozovek a komentářů
- Když řádek nejde zpracovat, do nazev napiš CHYBA a důvod
CSV: {DAVKA_MAX_30_RADKU}"""),
    ("Kontrolní checklist před importem",
     "Poslední brána. Chyby v parametrech stojí reklamace a vratky.",
     """Zkontroluj připravená produktová data před importem do e-shopu.
Pro každý produkt ověř a vypiš jen nálezy:
1) čísla a jednotky shodné se zdrojem dodavatele
2) žádný parametr, který ve zdroji není
3) název ≤ 80 znaků, meta description ≤ 155 znaků
4) HTML validní (uzavřené tagy, povolené tagy p, h3, ul, li, strong, table)
5) překlady: stejná čísla, kódy a značky jako v češtině
6) zákonné údaje (energetický štítek, bezpečnostní upozornění) nechybí, pokud je zdroj uvádí
Zdroj: {DATA_DODAVATELE}
Výstup: {PRIPRAVENA_DATA}"""),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def prompt_block(n, title, use, text):
    code = Paragraph(esc(text).replace("\n", "<br/>"), S["code"])
    box = Table([[code]], colWidths=[170 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SHEET),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([
        Paragraph(f'<font color="#2F5BEA">{n}.</font> {esc(title)}', S["h2"]),
        Paragraph(esc(use), S["use"]),
        box,
        Spacer(1, 7 * mm),
    ])


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Sans", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10 * mm, "AI Operátor pro e-shop · OK ENERGO s.r.o. · 15 promptů na produktové popisy a překlady")
    canvas.drawRightString(190 * mm, 10 * mm, f"{doc.page} / 6")
    canvas.restoreState()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm,
                            title="15 promptů na produktové popisy a překlady",
                            author="Michal Bašta – AI Operátor pro e-shop", subject="AI prompty pro e-shopy",
                            creator="AI Operátor")
    story = [
        Paragraph("15 promptů na produktové popisy a překlady", S["h1"]),
        Paragraph("Z feedu dodavatele hotový produkt za minutu. Prompty, které používám v provozu "
                  "e-shopu na Shoptetu napojeného na BaseLinker a Allegro.", S["lead"]),
        Paragraph("<b>Jak s prompty pracovat</b>", S["h2"]),
        Paragraph("1. Text v {SLOŽENÝCH ZÁVORKÁCH} nahraď svými daty. Ostatní nech beze změny.", S["p"]),
        Paragraph("2. Každý prompt obsahuje pravidlo „nic nedoplňuj“. Je to nejdůležitější řádek. "
                  "Bez něj si AI vymyslí parametry, které produkt nemá, a to znamená reklamace.", S["p"]),
        Paragraph("3. Začni na 10 produktech, porovnej výstup s dosavadními popisy a pravidla dolaď. "
                  "Pak teprve hromadně (prompt 14).", S["p"]),
        Paragraph("4. Překlady vždy zkontroluj druhým průchodem (prompt 8), ideálně jiným modelem.", S["p"]),
        Paragraph("5. Před importem pusť checklist (prompt 15). Funguje s ChatGPT, Claude i Gemini.", S["p"]),
        Spacer(1, 5 * mm),
        Paragraph("<b>Doporučený postup pro nový produkt</b>", S["h2"]),
        Paragraph("Feed dodavatele → 1 název → 4 parametry → 2 krátký popis → 3 dlouhý popis → 5 SEO → "
                  "6/7 překlady → 8 kontrola překladu → 15 checklist → import.", S["p"]),
        Spacer(1, 6 * mm),
    ]
    story.append(prompt_block(1, *PROMPTS[0]))
    story.append(PageBreak())
    # 14 zbylých promptů na 5 stran: 3,3,3,3,2
    chunks = [PROMPTS[1:4], PROMPTS[4:7], PROMPTS[7:10], PROMPTS[10:13], PROMPTS[13:15]]
    n = 2
    for i, chunk in enumerate(chunks):
        for p in chunk:
            story.append(prompt_block(n, *p))
            n += 1
        if i < len(chunks) - 1:
            story.append(PageBreak())
    story.append(Paragraph("<b>Chceš to nasadit na celý katalog?</b>", S["h2"]))
    story.append(Paragraph("Napiš mi. Pomůžu nastavit pravidla, glosář a hromadné zpracování "
                           "přímo pro tvůj e-shop a napojení (Shoptet, BaseLinker, Allegro).", S["p"]))
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(OUT, OUT.stat().st_size, "B")


if __name__ == "__main__":
    build()
