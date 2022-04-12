import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import re
import requests
import time

from mplsoccer import PyPizza, FontManager, add_image
from PIL import Image, ImageDraw
from urllib.request import urlopen
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

start = time.time()

font_normal = FontManager(("https://github.com/google/fonts/blob/main/apache/roboto/static/"
                           "Roboto-Regular.ttf?raw=true"))
font_italic = FontManager(("https://github.com/google/fonts/blob/main/apache/roboto/static/"
                           "Roboto-Italic.ttf?raw=true"))
font_bold = FontManager(("https://github.com/google/fonts/blob/main/apache/roboto/static/"
                         "Roboto-Medium.ttf?raw=true"))
print("Enter a player: ")
name = input()

options = Options()
options.add_argument("--log-level=3")
options.add_argument("--headless")
s = Service('C:\PythonProjects\chromedriver.exe')
driver = webdriver.Chrome(service=s, options=options)
driver.get('https://fbref.com/en/')

# Accept cookies
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
    By.XPATH,'//*[@class=" css-47sehv"]'
    ))).click()

try:
    search = driver.find_element(By.NAME, 'search')
    search.send_keys(name)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
        By.XPATH,"//span[@class='search-results-item']"
        ))).click()

    url = driver.current_url

    # Parsing name so input can be for e.g. Pogba and the output
    # on the picture will be the full name
    real_name = driver.find_element(
        By.XPATH, "//h1[@itemprop='name']"
        )

    # Player headshot img
    # Exception if headshot is missing from player
    try:
        image_url = driver.find_element(
            By.XPATH, "//img[@alt='" +real_name.text+ " headshot']"
            ).get_attribute('src')
    except Exception:
        pass

    # Player birthplace flag
    flag_url = driver.find_element(
        By.XPATH, "//span[@class='f-i']"
        ).get_attribute('style')
finally:
    #driver.close()
    pass

df = pd.read_html(url)
df_parsed = df[0]
df_parsed.drop([df_parsed.index[3], 
                df_parsed.index[4], 
                df_parsed.index[5], 
                df_parsed.index[7], 
                df_parsed.index[8], 
                df_parsed.index[9],
                df_parsed.index[13],
                df_parsed.index[15]
                ], inplace=True)
df_parsed.reset_index(inplace=True)
df_parsed.drop('index', axis='columns', inplace=True)

# Cropping circle picture
# Exception if headshot is missing from player
try:
    img = Image.open(urlopen(image_url)).convert("RGB")
    npImage = np.array(img)
    h,w = img.size
    alpha = Image.new('L', img.size,0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([0,0,h,w],0,360,fill=255)
    npAlpha=np.array(alpha)
    npImage=np.dstack((npImage,npAlpha))
    Image.fromarray(npImage).save('headshot.png')
    img_localfile = Image.open("headshot.png")
except Exception:
    pass

# Processing flag image url
pattern = '"(.*?)"'
flag_url_parsed = re.search(pattern, flag_url).group(1)

# Saving locally and converting SVG to PNG
with open('flag.svg', 'wb') as f:
    im = requests.get(flag_url_parsed, stream=True).content
    f.write(im)
flag_img_svg = svg2rlg("flag.svg")
renderPM.drawToFile(flag_img_svg, "flag.png", fmt="PNG")

params = df_parsed['Statistic']
values = df_parsed['Percentile']
slice_colors = ["#1A78CF"] * 4 + ["#FF9300"] * 4 + ["#D70232"] * 6      # Attacking, Possession and Defending slice colors
text_colors = ["#000000"] * 8 + ["#F2F2F2"] * 6                         # Attacking/Possession and Defending text colors

baker = PyPizza(
    params=params,                  # list of parameters
    background_color="#222222",     # background color
    straight_line_color="#000000",  # color for straight lines
    straight_line_lw=1,             # linewidth for straight lines
    last_circle_color="#000000",    # color for last line
    last_circle_lw=1,               # linewidth of last circle
    other_circle_lw=0,              # linewidth for other circles
    inner_circle_size=20            # size of inner circle
)

fig, ax = baker.make_pizza(
    values,                          # list of values
    figsize=(8, 8),                  # adjust figsize according to your need
    color_blank_space="same",        # use the same color to fill blank space
    slice_colors=slice_colors,       # color for individual slices
    value_colors=text_colors,        # color for the value-text
    value_bck_colors=slice_colors,   # color for the blank spaces
    blank_alpha=0.4,                 # alpha for blank-space colors
    param_location=105,              # where the parameters will be added
    kwargs_slices=dict(
        facecolor="#33ceff", edgecolor="#000000",
        zorder=2, linewidth=1
    ),                               # values to be used when plotting slices
    kwargs_params=dict(
        color="#F2F2F2", fontsize=10,
        fontproperties=font_normal.prop, va="center"
    ),                               # values to be used when adding parameter
    kwargs_values=dict(
        color="#000000", fontsize=11,
        fontproperties=font_normal.prop, zorder=3,
        bbox=dict(
            edgecolor="#000000", facecolor="#33ceff",
            boxstyle="round,pad=0.2", lw=1
        )
    )                                # values to be used when adding parameter-values
)

# title name of player
fig.text(
    0.515, 0.97, str(real_name.text), size=18,
    ha="center", fontproperties=font_bold.prop, color="#F2F2F2"
)

# description title
fig.text(
    0.515, 0.932,
    "per 90 Percentile Rank vs Positional Peers in Top 5 Leagues | 365 Days",
    size=15,
    ha="center", fontproperties=font_bold.prop, color="#F2F2F2"
)

# text rectangles
fig.text(
    0.30, 0.03, "Attacking        Possession       Defending", size=14,
    fontproperties=font_bold.prop, color="#F2F2F2"
)

# rectangles
fig.patches.extend([
    plt.Rectangle(
        (0.27, 0.03), 0.025, 0.021, fill=True, color="#1a78cf",
        transform=fig.transFigure, figure=fig
    ),
    plt.Rectangle(
        (0.422, 0.03), 0.025, 0.021, fill=True, color="#ff9300",
        transform=fig.transFigure, figure=fig
    ),
    plt.Rectangle(
        (0.592, 0.03), 0.025, 0.021, fill=True, color="#d70232",
        transform=fig.transFigure, figure=fig
    ),
])

# image player headshot
try:
    ax_image = add_image(
        img_localfile, fig, left=0.4478, bottom=0.4315, width=0.13, height=0.127
    )
except Exception:
    pass

# image player flag
# flag img if/elif so it aligns a little better with title
flag_img = Image.open("flag.png")
name_length = len(str(real_name.text))

def flagimager(leftlength):
    ax_image = add_image(
    flag_img, fig, left=leftlength, bottom=0.97, width=0.032, height=0.024, interpolation='hanning'
    )

if name_length > 18:
    flagimager(0.40)
elif name_length >= 16:
    flagimager(0.38)
elif name_length >= 14:
    flagimager(0.36)
elif name_length >= 12:
    flagimager(0.35)
else:
    flagimager(0.34)

end = time.time()
print(end - start)

plt.show()

