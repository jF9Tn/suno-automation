import sys
import os
import json
import re

from browserforge.fingerprints import Screen
from camoufox.sync_api import Camoufox

if __name__ == "__main__" and not __package__:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from backend.lib.supabase import supabase
from backend.utils.assign_styles import get_style_by_chapter
from backend.utils.bible_utils import split_chapter_into_sections
from backend.utils.llm_chat_backup import aimlapi_general_query
from backend.utils.llm_chat_utils import llm_general_query
from backend.utils.converter import song_strcture_to_lyrics

book_name = "Genesis"
book_chapter = 1

response = (
    supabase.table("song_structure_tbl")
    .select("verse_range")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .execute()
)

verse_ranges = []

if response.data is not None and len(response.data) == 0:
    print("No data found in Supabase, proceeding to split chapter.")
    split_chapter = split_chapter_into_sections(book_name, str(book_chapter))
    prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into {split_chapter} sections of similar size which stand alone. Give the range of verses separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not iclude the thinking and thought process to save output tokens."
    verse_ranges_str = llm_general_query(prompt)

    if not verse_ranges_str:
        print("Primary LLM failed, trying backup LLM...")
        verse_ranges_str = aimlapi_general_query(prompt)

    if verse_ranges_str:
        verse_ranges = verse_ranges_str.split(",")
        print(type(verse_ranges))
        print(f"Verse ranges: {verse_ranges}")

        if verse_ranges:
            print(f"First verse range: {verse_ranges[0]}")
        else:
            print("Error: verse_ranges is empty after splitting.")
    else:
        print(
            "Error: Failed to get verse ranges from LLM. Skipping further processing."
        )
        verse_ranges = []

    for verse_range in verse_ranges:
        supabase.table("song_structure_tbl").insert(
            {
                "book_name": book_name,
                "chapter": book_chapter,
                "verse_range": verse_range,
            }
        ).execute()
else:
    print("Data found in Supabase, no need to split chapter.")
    for item in response.data:
        verse_ranges.append(item["verse_range"])

print(f"Verse ranges from Supabase: {verse_ranges}")

response = (
    supabase.table("song_structure_tbl")
    .select("verse_range")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .is_("song_structure", None)
    .execute()
)

print(f"Response from Supabase: {response}")

if response.data is not None and len(response.data) > 0:
    for verse_range in verse_ranges:
        song_structure = {}
        passage_tone = 0
        styles = []

        prompt = f"Outline the Book of '{book_name}' Chapter '{book_chapter}' Verses '{verse_range}' in the bible as a song structure of 4-6 naturally segmented verses, choruses or bridges. Don't write out the text. Never split one verse across stanzas. Never reuse verses. Give no introduction, conclusion or explanation, simply give scripture ranges separated by commas. For each, Label your stanzas inside brackets[] followed by a colon : and followed by only verse range like 5-14, each separated by comma in a single line. give nothing else. example: [Chorus]:18-28,[Bridge]:29-35"

        prompt = "Make a song structure using the Book of Genesis chapter 1, strictly from verses 1-5 in the Bible only. The song will have 4-6 naturally segmented either verses, choruses or bridges. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}. Do not provide any explanation only the json output."

        song_structure = llm_general_query(prompt)
        if not song_structure:
            print("Primary LLM failed, trying backup LLM...")
            song_structure = aimlapi_general_query(prompt)
        print(f"Song structure: {song_structure}")

        song_structure_dict = song_structure

        print(f"Song structure dict: {song_structure_dict}")

        prompt = f"Analyze the overall Bible passage is positive or negative: {song_structure_dict}. Strictly the output should be 0 or 1 only. 0 for negative and 1 for positive. Do not provide any explanation only the number."

        passage_tone = llm_general_query(prompt)
        if not passage_tone:
            print("Primary LLM failed, trying backup LLM...")
            passage_tone = aimlapi_general_query(prompt)
        print(f"Passage tone: {passage_tone}")

        styles = get_style_by_chapter(book_name, book_chapter, int(passage_tone))
        print(f"Style for {book_name} {book_chapter}: {styles}")

        supabase.table("song_structure_tbl").update(
            {
                "song_structure": str(song_structure_dict),
                "tone": int(passage_tone),
                "styles": styles,
            }
        ).eq("book_name", book_name).eq("chapter", book_chapter).eq(
            "verse_range", verse_range
        ).execute()

song_structure_dict = (
    supabase.table("song_structure_tbl")
    .select("song_structure")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .execute()
)

song_structure_json_string = song_structure_dict.data[0]["song_structure"]
parsed_song_structure = json.loads(song_structure_json_string)

song_structure_verses = song_strcture_to_lyrics(
    parsed_song_structure, book_name, book_chapter
)
print(f"Converted song structure verses: {song_structure_verses}")

lyrics_parts = []
for section_title, verses_dict in song_structure_verses.items():
    lyrics_parts.append(f"[{section_title}]:")
    for verse_num, verse_text in verses_dict.items():
        processed_text = verse_text.strip()
        processed_text = re.sub(r"\s*([.;])\s*", r"\1\n\n", processed_text)
        processed_text = re.sub(r"^\s+(?=\S)", "", processed_text, flags=re.MULTILINE)
        lyrics_parts.append(processed_text)

intermediate_lyrics = "\n".join(lyrics_parts)
lyrics = re.sub(r"\n{3,}", "\n", intermediate_lyrics)
lyrics = re.sub(r"\n", "\n\n", lyrics)
lyrics = re.sub(r"(\[.*?\]:)\n+", r"\1\n", lyrics)

print(lyrics)


os_list = ["windows", "macos", "linux"]
font_list = ["Arial", "Helvetica", "Times New Roman"]
constrains = Screen(max_width=1920, max_height=1080)


with Camoufox(
    screen=constrains,
    humanize=True,
    main_world_eval=True,
    geoip=True,
) as browser:
    page = browser.new_page(locale="en-US")
    page.goto("https://suno.com")
    page.wait_for_load_state(
        "networkidle"
    )  # Wait for network to be idle    # Debug: Check what's on the page
    print("Debugging: Looking for sign in elements...")
    page.screenshot(path="debug_before_signin.png")

    # Try multiple selectors for the sign in button
    sign_in_selectors = [
        'button:has(span:has-text("Sign in"))',
        'button[data-testid*="signin"]',
        'button:has-text("Sign in")',
        'button:text("Sign in")',
        '[role="button"]:has-text("Sign in")',
        'a:has-text("Sign in")',
        '*:has-text("Sign in")',
    ]

    sign_in_button_selector = None

    for selector in sign_in_selectors:
        try:
            print(f"Trying selector: {selector}")
            count = page.locator(selector).count()
            print(f"Found {count} elements with selector: {selector}")

            if count > 0:
                # Check if element is visible
                is_visible = page.locator(selector).first.is_visible()
                print(f"First element visible: {is_visible}")

                if is_visible:
                    sign_in_button_selector = selector
                    print(f"Using selector: {selector}")
                    break
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue

    if not sign_in_button_selector:
        print("No suitable sign in button found. Available buttons:")
        # Get all buttons on the page for debugging
        all_buttons = page.locator("button").all()
        for i, button in enumerate(all_buttons):
            try:
                text = button.text_content()
                print(f"Button {i}: '{text}' - visible: {button.is_visible()}")
            except Exception as e:
                print(f"Error getting button {i} info: {e}")

        # Get all links that might be sign in
        all_links = page.locator("a").all()
        for i, link in enumerate(all_links):
            try:
                text = link.text_content()
                if "sign" in text.lower() or "login" in text.lower():
                    print(f"Link {i}: '{text}' - visible: {link.is_visible()}")
            except Exception as e:
                print(f"Error getting link {i} info: {e}")

        raise Exception("Could not find sign in button")

    # Wait for the selected button to be visible and enabled
    page.wait_for_selector(sign_in_button_selector, state="visible", timeout=60000)
    # For buttons that support disabled property, check if enabled
    # Use a more compatible approach for checking if button is enabled
    try:
        # Simpler approach - just check if we can click the element
        page.locator(sign_in_button_selector).first.wait_for(
            state="visible", timeout=10000
        )
        print("Sign in button is visible and should be clickable")
    except Exception as e:
        print(f"Could not wait for button to be fully ready, proceeding anyway: {e}")

    print(f"Clicking sign in button with selector: {sign_in_button_selector}")
    page.click(sign_in_button_selector)
    page.wait_for_timeout(2000)
    page.click('button:has(img[alt="Sign in with Google"])')
    page.wait_for_timeout(2000)
    page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    page.type('input[type="password"]', "&!8G26tlbsgO")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    page.click('button:has(span:has-text("Custom"))')
    page.wait_for_timeout(2000)
    page.type('textarea[data-testid="lyrics-input-textarea"]', "test lyrics")
    page.wait_for_timeout(2000)
    page.type('textarea[data-testid="tag-input-textarea"]', "test, song, lyrics")
    page.wait_for_timeout(2000)
    page.type('input[placeholder="Enter song title"]', "test title")
    page.wait_for_timeout(2000)
    page.click('button:has(span:has-text("Create"))')
    page.wait_for_timeout(2000)
    # print("Waiting for 2 seconds before checking the number of elements...")
    # page.goto("https://suno.com/me", wait_until="domcontentloaded", timeout=30000)
    # print(f"Navigation to /me initiated. Current URL: {page.url}")
    # page.wait_for_url("https://suno.com/me**", timeout=20000)

    # # Debug: Check what songs are available
    # print("Debugging: Looking for available songs...")
    # page.screenshot(path="debug_songs_page.png")

    # # Look for all song titles
    # all_song_titles = page.locator("span.text-foreground-primary[title]").all()
    # print(f"Found {len(all_song_titles)} songs with titles:")
    # for i, song in enumerate(all_song_titles):
    #     try:
    #         title = song.get_attribute("title")
    #         is_visible = song.is_visible()
    #         print(f"Song {i}: '{title}' - visible: {is_visible}")
    #     except Exception as e:
    #         print(f"Error getting song {i} info: {e}")

    # # Try to find the "test title" song
    # locator = page.locator('span.text-foreground-primary[title="test title"]')
    # try:
    #     locator.first.wait_for(state="attached", timeout=10000)
    #     count = locator.count()
    #     print(f"Found {count} songs with title 'test title'")
    #     # Check if they are visible and find the first visible one
    #     visible_song_index = -1
    #     for i in range(count):
    #         try:
    #             is_visible = locator.nth(i).is_visible()
    #             print(f"Song {i} with 'test title' - visible: {is_visible}")
    #             if is_visible and visible_song_index == -1:
    #                 visible_song_index = i
    #         except Exception as e:
    #             print(f"Error checking visibility of song {i}: {e}")

    #     page.wait_for_timeout(2000)

    #     if visible_song_index >= 0:
    #         print(f"Right-clicking on visible song at index {visible_song_index}")
    #         locator.nth(visible_song_index).click(button="right")
    #     else:
    #         print(
    #             "No visible songs with 'test title' found, trying to scroll to make some visible"
    #         )
    #         # Try to scroll the page to reveal more songs
    #         try:
    #             page.evaluate("window.scrollTo(0, 0)")  # Scroll to top
    #             page.wait_for_timeout(1000)
    #             page.evaluate("window.scrollBy(0, 500)")  # Scroll down a bit
    #             page.wait_for_timeout(1000)

    #             # Check again for visible songs
    #             for i in range(count):
    #                 try:
    #                     is_visible = locator.nth(i).is_visible()
    #                     if is_visible:
    #                         print(f"After scrolling, found visible song at index {i}")
    #                         locator.nth(i).click(button="right")
    #                         visible_song_index = i
    #                         break
    #                 except Exception as e:
    #                     print(
    #                         f"Error checking visibility after scroll for song {i}: {e}"
    #                     )

    #             if visible_song_index == -1:
    #                 raise Exception(
    #                     "No visible songs with 'test title' found even after scrolling"
    #                 )
    #         except Exception as scroll_error:
    #             print(f"Error during scrolling attempt: {scroll_error}")
    #             raise Exception("No visible songs with 'test title' found")

    # except Exception as e:
    #     print(f"Error finding 'test title' songs: {e}")
    #     print("Trying to find any available song to download...")

    #     # Fallback: try to find any song
    #     any_song = page.locator("span.text-foreground-primary[title]").first
    #     if any_song.is_visible():
    #         print("Found alternative song, right-clicking on it")
    #         any_song.click(button="right")
    #     else:
    #         raise Exception("No songs found to download")
    # page.wait_for_timeout(2000)

    # context_menu_content = page.locator(
    #     "div[data-radix-menu-content][data-state='open']"
    # )
    # context_menu_content.wait_for(state="visible", timeout=15000)
    # page.wait_for_timeout(500)

    # download_submenu_trigger = context_menu_content.locator(
    #     '[data-testid="download-sub-trigger"]'
    # )
    # download_submenu_trigger.wait_for(state="visible", timeout=5000)
    # download_submenu_trigger.hover()

    # download_trigger_id = download_submenu_trigger.get_attribute("id")
    # if not download_trigger_id:
    #     raise Exception(
    #         "Download trigger item does not have an ID. Cannot reliably locate submenu."
    #     )

    # download_submenu_panel = page.locator(
    #     f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
    # )

    # download_submenu_panel.wait_for(state="visible", timeout=10000)

    # mp3_audio_item = download_submenu_panel.locator(
    #     "div[role='menuitem']:has-text('MP3 Audio')"
    # )

    # mp3_audio_item.wait_for(state="visible", timeout=5000)

    # mp3_audio_item.click()
    # page.wait_for_timeout(2000)

    # download_bttn = page.locator('button:has(span:has-text("Download Anyway"))')

    # with page.expect_download(timeout=30000) as download_info:
    #     download_bttn.click()
    # download = download_info.value

    # download_path = f"./{download.suggested_filename}"
    # download.save_as(download_path)
    # print(f"Clicked 'MP3 Audio'. Download started and saved to: {download_path}")

    page.wait_for_timeout(3000)
    page.close()
