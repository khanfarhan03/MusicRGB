"""Generate the user-facing guide beside the packaged executable."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether,
)

BASE = Path(__file__).resolve().parent
OUT = BASE / "dist" / "MusicRGB-User-Guide.pdf"
INK = colors.HexColor("#20263b")
PURPLE = colors.HexColor("#6545b5")
MUTED = colors.HexColor("#596276")
PALE = colors.HexColor("#f3f0fa")
LINE = colors.HexColor("#e2e5ee")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="GuideTitle", fontName="Helvetica-Bold", fontSize=29,
    leading=33, textColor=INK, spaceAfter=13))
styles.add(ParagraphStyle(name="GuideHeading", fontName="Helvetica-Bold", fontSize=14,
    leading=18, textColor=PURPLE, spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="GuideBody", fontName="Helvetica", fontSize=10,
    leading=14.5, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name="GuideSmall", fontName="Helvetica", fontSize=9,
    leading=12.5, textColor=MUTED, spaceAfter=5))
styles.add(ParagraphStyle(name="GuideCell", fontName="Helvetica", fontSize=9.2,
    leading=13, textColor=INK))
styles.add(ParagraphStyle(name="GuideWhite", fontName="Helvetica-Bold", fontSize=9.2,
    leading=13, textColor=colors.white))
story = []


def p(text, style="GuideBody"):
    return Paragraph(text, styles[style])


def title(number, heading, intro):
    story.append(p("MUSIC RGB IMMERSIVE  /  GUIDE " + number, "GuideSmall"))
    story.append(p(heading, "GuideTitle"))
    story.append(p(intro))


def heading(text):
    story.append(p(text, "GuideHeading"))


def table(headers, rows, widths):
    data = [[p(h, "GuideWhite") for h in headers]]
    data.extend([[p(cell, "GuideCell") for cell in row] for row in rows])
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), .5, PURPLE),
    ]))
    story.append(t)


def note(text):
    t = Table([[p(text)]], colWidths=[499])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(Spacer(1, 9))
    story.append(t)


def footer(canvas, doc):
    canvas.setStrokeColor(LINE)
    canvas.line(48, 42, A4[0]-48, 42)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(48, 28, "Music RGB  |  ASUS Vivobook 16 X1605VA  |  16 October 2026")
    canvas.drawRightString(A4[0]-48, 28, str(doc.page))


title("01", "Start with the music", "A practical guide to the effects and controls in Music RGB. "
      "Works with audio from Spotify, YouTube, games and local players through your selected Windows output.")
heading("Your first session")
for label, text in [
    ("1. Open the app", "Run <b>Setup.cmd</b> once, then open <b>Launch.cmd</b>. Setup installs the app's Python dependencies."),
    ("2. Turn on the keyboard backlight", "Use the laptop's normal keyboard brightness controls. Software colours will not be visible if the hardware backlight is turned off."),
    ("3. Choose the output playing your music", "Use the audio dropdown. For speakers, try <b>Speakers (Realtek(R) Audio)</b>. With SteelSeries Sonar, select the channel carrying the music, such as Gaming, or its physical output."),
    ("4. Choose an effect and start", "Select <b>Song vibe</b> for a gradual response to the music's character, then click <b>Start sync</b>. Play a song and allow several seconds for it to settle."),
    ("5. Adjust the feel", "Start with sensitivity around <b>1.0</b>, brightness around <b>0.75</b> and smoothness around <b>0.65</b>. Lower smoothness for a sharper response; raise it for softer fades."),
]:
    story.append(KeepTogether([p(label, "GuideHeading"), p(text)]))
note("<b>This Vivobook has a white backlight.</b> Music RGB changes its intensity using the available keyboard brightness levels. Color names control the preview and are translated to white intensity on the laptop.")
heading("What you see")
story.append(p("The small keyboard preview shows the white intensity being calculated. The bars show the audio spectrum. "
    "In Song vibe, the label describes the estimated audio character. With Preview only enabled, the display responds while the hardware stays out of the live animation."))
story.append(p("<b>Hardware limit:</b> the X1605VA keyboard is backlit, not RGB. It cannot show colored lighting effects; all keys stay white.", "GuideSmall"))
story.append(PageBreak())

title("02", "Choose an effect", "Start with the sound you want to emphasise. The effects below change the white backlight intensity; colors appear in the preview only.")
table(["Effect", "How it behaves"], [
    ("<b>Song vibe</b>", "Uses a slowly changing palette based on audio energy and the balance of bass, mids and treble. Gentle pulses follow estimated bass onsets."),
    ("<b>Spectrum</b>", "Preview color follows the frequency balance: bass leans red, mids green and treble blue. Keyboard intensity follows the audio."),
    ("<b>Bass pulse</b>", "Emphasises low-frequency energy. Uses your chosen palette and grows brighter with stronger bass."),
    ("<b>Beat bloom</b>", "Moves to another preview palette colour on an estimated bass onset, then fades. Keyboard intensity responds to the onset."),
    ("<b>Rainbow</b>", "Cycles through hues in the preview while music controls keyboard intensity. Animation speed changes how quickly preview hues cycle."),
    ("<b>Aurora</b>", "Drifts through your palette with small bass-driven changes. Try it for a softer background glow."),
    ("<b>Ember</b>", "Uses red and amber tones that brighten and warm with the music."),
    ("<b>Ocean</b>", "Uses blue and teal tones with bass and onset accents."),
    ("<b>Custom colour</b>", "Keeps your chosen hue while audio controls its brightness. Choose custom colour opens the colour picker and selects this effect."),
], [112, 387])
heading("How Song vibe chooses colours")
story.append(p("Colors describe the on-screen preview. The physical X1605VA keyboard stays white and changes brightness in discrete hardware steps.", "GuideSmall"))
story.append(p("It listens to several seconds of audio rather than stepping through a timed rainbow. "
    "Softer passages lean blue/violet, bass-heavy passages magenta, prominent mids amber and energetic treble teal. "
    "The palette changes gradually so a passage keeps a consistent visual feel."))
note("<b>An estimate from the sound, not emotional understanding.</b> Song vibe does not read lyrics, genre, album art or Spotify metadata. "
    "Playback volume and audio processing affect its estimate. Beat bloom detects approximate bass onsets; it does not track an exact BPM or song beat grid.")
story.append(PageBreak())

title("03", "Shape the response", "Controls update while sync runs. Change one at a time so you can hear and see what it does.")
table(["Control", "What to change"], [
    ("<b>Sensitivity</b><br/>0.2 to 4.0", "Raise it if the response is too weak. Lower it if brightness stays near its maximum. It changes the lighting response, not the playback volume."),
    ("<b>Brightness</b><br/>0.0 to 1.0", "Caps the live effect's intensity. This is separate from the laptop's hardware backlight setting."),
    ("<b>Smoothness</b><br/>0.0 to 1.0", "Higher values give slower fades and softer preview transitions. Lower values follow changes more sharply."),
    ("<b>Animation speed</b><br/>0.2 to 3.0", "Changes Rainbow and Aurora preview speed and the minimum spacing between onset reactions. It does not change playback speed."),
    ("<b>Silence threshold</b><br/>0.000 to 0.020", "Raise it slightly if quiet background audio keeps triggering light. Too high a threshold can hide quiet musical passages."),
    ("<b>Glow during silence</b><br/>0.00 to 0.30", "Sets a minimum glow while sync is running. Set it to zero for a fade to darkness when music pauses. The separate stop colour applies after Stop."),
    ("<b>Colour palette</b>", "Neon, Sunset, Ice, Forest or Candy. Changes the preview for Bass pulse, Beat bloom and Aurora. Song vibe chooses its own preview colors from the audio."),
    ("<b>Preview only</b>", "Runs the on-screen preview without live keyboard writes. If switched on during hardware sync, the selected stop colour is applied once before releasing control."),
    ("<b>When sync stops</b>", "Light blue (default), White, Dim purple, Off, Keep last or Custom colour. These choices map to available white backlight intensity levels."),
    ("<b>Keep window on top</b>", "Keeps the control panel above other windows. It does not affect the lighting or audio."),
], [126, 373])
note("<b>Two useful starting points:</b> choose the <b>Chill</b> preset for softer fades and a faint idle glow. "
    "Choose <b>Immersive</b> for stronger onset reactions. Presets replace selected controls, so check your final settings after applying one.")
story.append(PageBreak())

title("04", "Save it. Keep it running.", "Presets store a look you can reuse. Tray controls let music sync continue with the main window hidden.")
heading("Presets and remembered settings")
story.append(p("Use the preset dropdown for <b>Song vibe, Balanced, Bass night, Immersive, Chill</b> or <b>Warm glow</b>. "
    "Built-in presets adjust selected controls; they do not reset every setting."))
story.append(p("<b>Save preset...</b> exports the current settings to a named JSON file. Keep as many files as you want. "
    "Use <b>Load...</b> to restore one. Loading keeps your current audio output, preview choice and window-on-top setting."))
story.append(p("<b>Save settings</b> remembers the current controls for the next session. Quitting also saves them. "
    "The app does not automatically start audio capture when reopened."))
heading("The icon beside the Windows clock")
story.append(p("Click <b>Hide to tray</b> to hide the window while sync continues. Right-click the Music RGB icon "
    "beside the clock for <b>Show controls, Start / resume, Stop</b> or <b>Quit</b>. If the icon is tucked away, look in Windows' hidden tray icons."))
story.append(p("<b>Closing the main window quits the app.</b> To keep the effect running, use Hide to tray instead. "
    "The app does not install a task to start with Windows."))
heading("If something does not respond")
table(["Symptom", "Try this"], [
    ("No response to music", "Check that the selected output is actually carrying the music. Try the physical speaker output or the correct Sonar channel. Ensure Preview only is off."),
    ("Preview moves, keyboard stays dark", "Raise hardware keyboard brightness. Check live Brightness is above zero. If another app controls lighting, turn off its active effect."),
    ("Headphones or output changed", "Stop sync, connect/select the new output, click Refresh outputs, then start again."),
    ("Driver access denied", "Close the app, then right-click MusicRGB-MusicWave.exe and choose Run as administrator."),
    ("Lights flicker or look too busy", "Increase Smoothness, reduce Sensitivity or choose Song vibe / Chill. Avoid running another lighting controller at the same time."),
], [139, 360])
heading("Privacy and keyboard lighting")
story.append(p("Audio is analysed locally in memory. It is not saved or uploaded. No Spotify login is needed. "
    "All sounds on the selected playback output, including notifications, can affect the lights. "
    "Protected or exclusive playback may not provide usable audio capture.", "GuideSmall"))
story.append(p("The app does not remember the keyboard brightness that was active before sync. The selected stop behavior sets the white backlight when sync ends.", "GuideSmall"))

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=48, leftMargin=48,
    topMargin=42, bottomMargin=58, title="Music RGB Immersive - User Guide",
    author="Music RGB", subject="Features, setup, presets and troubleshooting")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
